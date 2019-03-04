# CameraOrganizer
Organize photos and videos from a flat-directory into a year and date-sorted directory structure.

Compatible with the following image and video formats:
jpg, gif, png, mp4, mov

### Usage:
python CameraOrganizer.py <.json config file>

Config file format is:
{
    "source":<location to find images and videos>,
    "library":<location to move images and videos into year and date-sorted folders>
}

CameraOrganizer.bat will run the command from Windows GUI.