P4Info to Java constants tool
====

Generates ONOS Java constants according to the P4 Info file.

Dependencies:
 - Python2.7 or higher
 - protobuf 3.2.x python package

Usage:
```$ gen_constants.py BaseName P4InfoFilePath [CopyrightAndConstantsFile]```

When the optional copyright and constants file is specified its contents will
be read and included in the generated output. If it starts with
a ```/* single or multi line text */``` style comment that comment will be
the first of the generated output. Any lines after the comment, or all
lines in case the file does not start with a comment, will be placed
after the class definition. It can be used to specify the constants used
in the P4 source that are not included in the P4 info file.  
