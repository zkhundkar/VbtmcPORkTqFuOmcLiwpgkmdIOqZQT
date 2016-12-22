# SvnLink

This windows service (Python 2.7) is half of a multi-platform document backup and synchronization with a remote subversion repository.

The service pulls content from multiple remote computers (targets), compares and updates correspnding files in a series of folders that are the local working copy folders of a set of remote subversion repositories. The comparator handles both text and binary files. The targets maintain a log of file changes and only modified files are retrieved. An ascii (text) file that is retrieved will always be used to overwrite the local copy (and the local copy's modified timestamp will be set to that of the copy on the target; a binary file retrieved will be compared byte-wise and used to overwrite the local copy only if the two copies are different.

The service can be configured to run upto once an hour and no less than once a day at midnight. It can also be configured to do auto-commits when the local copies are updated from the files retrieved from a remote target. 


 ## Usage ##
The content included here is for review only. Please do not fork.

If you wish to review this project in detail, please send me an email with your contact information (valid email), and your intended use. 

## License ##
All rights reserved
