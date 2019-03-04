import argparse
import os
import json
import sys
import exifread
import time

# Debug
import subprocess


accepted_extensions = ['jpg', 'gif', 'png', 'mp4', 'mov']

def qualify_file(filename):
	extension = os.path.splitext(filename)[1][1:]
	if extension in accepted_extensions:
		return (True)
	else:
		return (False)		

class Item:
	def __init__(self, filename, path):
		self.filename = filename
		self.extension = ''.join(filename.split('.')[1:])
		self.path = path
		
		handled = False;
		
		if filename.endswith('.jpg'):
			tags = {}
			with open(self.get_src_file(), 'rb') as f:
				tags = exifread.process_file(f)
				
			exif_datetime = tags.get('EXIF DateTimeOriginal')
			if exif_datetime is not None:
				# Prefer the Original Date/Time EXIF tag, if it exists.
				self.ts = time.strptime(str(exif_datetime), '%Y:%m:%d %H:%M:%S')
				handled = True;
				
		if handled is not True:
			# The Creation timestamp will have been set to when the image was
			# copied; not when it was taken.
			# The Modification timestamp is a decent subsitute, as long as it
			# hasn't been rotated. For this reason, do any rotations after
			# processing.
			self.ts = time.localtime(os.path.getmtime(self.get_src_file()))

	def get_src_file(self):
		return "{path}\\{filename}".format(path=self.path, filename=self.filename)

	def get_src_info(self):
		return "{filename} {src_file} {date}".format(filename=self.filename, src_file=self.get_src_file(), date=time.strftime("%Y-%m-%d %H-%M-%S", self.ts))
		
	def get_filename(self):
		return "{date}_{time}.{extension}".format(date=time.strftime("%Y%m%d", self.ts), time=time.strftime("%H%M%S", self.ts), extension=self.extension)
		
	def get_year(self):
		return "{year}".format(year=time.strftime("%Y", self.ts))
	
	def get_date(self):
		return "{date}".format(date=time.strftime("%Y-%m-%d", self.ts))
		

def analyze_directory(target_dir):
	# Analyze files in source directory.
	year_dict = dict()
	for (dirpath, dirnames, filenames) in os.walk(target_dir):
		for filename in filenames:
			if qualify_file(filename):
				# This is a file we're interested in.
				item = Item(filename, dirpath)
				
				# Sort it into year/date groups.
				if item.get_year() not in year_dict:
					# Year does not exist. Populate it with a date dictionary.
					year_dict[item.get_year()] = dict()
				
				if item.get_date() not in year_dict[item.get_year()]:
					# Date does not exist. Populate it with an empty item list.
					year_dict[item.get_year()][item.get_date()] = []
				
				# Add the item to the correct list.
				year_dict[item.get_year()][item.get_date()].append(item)
	
	#print("Analyzed Files:")
	#for year, date_dict in year_dict.items():
	#	print(year)
	#	for date, item_list in year_dict[year].items():
	#		print(date)
	#		for item in item_list:
	#			print (item.get_filename())
				
	return year_dict
	

def archive_new_media(target_dir, year_dict):
	# Process new years.
	for new_year, date_dict in year_dict.items():
		year_path = "{path}\\{year}".format(path=target_dir, year=new_year)
		
		# Create the year directory if it doesn't already exist.
		if not os.path.isdir(year_path):
			os.makedirs(year_path)
		
		# Find out what dates are currently in the year directory.
		existing_dates = [date_entry for date_entry in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, date_entry))]
		
		# Process new dates.
		for new_date, item_list in year_dict[new_year].items():
			# Don't copy existing dates.
			if any(new_date in subdir for subdir in existing_dates):
				print("Skipping media from {date}".format(date=new_date))
			else:
				print("Archiving media from {date}".format(date=new_date))
				date_path = "{year_path}\\{date}".format(year_path=year_path, date=new_date)
			
				# Create the date directory if it doesn't already exist.
				if not os.path.isdir(date_path):
					os.makedirs(date_path)

				# Move new media items to target directory.
				for item in item_list:
					os.rename(item.get_src_file(), os.path.join(date_path, item.get_filename()))
	
def main():
	parser = argparse.ArgumentParser(description='Put photos and vidoes into date-sorted folders.')
	
	parser.add_argument('config', help='Configuration file')
	parser.add_argument('--remove', help='Remove source files', action='store_true')

	args = parser.parse_args()
	
	try:
		with open(args.config) as json_f:
			cfg = json.load(json_f)

			# Check for a correctly constructed config file.

			# Source directory from which we get media.
			source_dir = cfg['source']
			if source_dir is not None:
				source_ok = os.path.isdir(source_dir)
			else:
				source_ok = False

			# Library to which media will be copied.
			library_dir = cfg['library']
			if library_dir is not None:
				library_ok = os.path.isdir(library_dir)
			else:
				library_ok = False

			# Report any problems with the config.
			config_valid = source_ok and library_ok
			if not config_valid:
				print('Problem with configuration file.')
				if source is None:
					print(' source: is missing')
				else:
					print(' source directory is {src}'.format(src="valid" if source_ok else "invalid"))

				if library is None:
					print(' library: is missing')
				else:
					print(' library directory is {lib}'.format(lib="valid" if library_ok else "invalid"))
				sys.exit(0)

			# Analyze source media.
			new_media = analyze_directory(source_dir)
			
			# Copy files to year/year-month-date sorted directories.
			archive_new_media(library_dir, new_media)
		
			print("Archiving complete")
		
	except FileNotFoundError as e:
		print("File \"{}\" did not exist!".format(args.config))
		
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(type(e), e, '-', fname, exc_tb.tb_lineno)

		
if __name__ == "__main__":
    # execute only if run as a script
    main()
