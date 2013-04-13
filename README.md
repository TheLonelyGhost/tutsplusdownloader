TutsPlusDownloader
==================

This Python module is a (*cough*) proof-of-concept that can (theoretically) download content from TutsPlus Premium. The TutsPlusDownloader module should theoretically be easier on the Envato servers given its non-threaded, caching nature and that it sets login cookies a single time per downloading session. If properly used it should download all links from a file during a single downloading session.

----

This class is primarily intended for (theoretically) downloading TutsPlus Premium courses. The process goes like so:

1. Login using supplied credentials and verify logged-in status.
2. Create a table of contents composed of all lessons within each section. Stored as `README.txt` in the base of the specified download directory.
3. If available, download entire course as a single file.
4. Else, loop through each lesson page and download video and project files. Files will be named by the lesson title and put in directories according to section.

If an eBook link is supplied, the process is far simpler:

1. Login using supplied credentials and verify logged-in status.
2. Download ZIP of ebook(s) to a directory named after the ebook.

**WARNING!** It is explicitly against TutsPlus terms of service to use scripts to access their website. Since this module is strictly intended for academic purposes, The user takes all responsibility for any actions resulting from actual use of this module or any derivation of it.