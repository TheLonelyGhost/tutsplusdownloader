#!/usr/bin/env python

import sys, string, requests, re, os, errno, codecs
from bs4 import BeautifulSoup

class TutsPlusDownloader:
    table_of_contents = ''
    HTML = {'course': '', 'lesson': '', 'ebook': ''}
    TEXT = {'course': '', 'section': '', 'lesson': '', 'ebook': ''}
    e_soup = ''
    c_soup = ''
    l_soup = ''
    LESSON_NUM = 0
    DOWNLOAD_LOCATION = ''
    COURSE_DL_LOCATION = ''
    USERNAME = ''
    PASSWORD = ''
    REPORTING = 9
    
    def parseDownloadsList(self, fileLocation):
        self.broadcast('Using links from "' + fileLocation + '" ...')
        self.debug('Parsing links file')
        f = open(fileLocation)
        lines = f.readlines()
        f.close()
        
        self.debug('Removing duplicate links ...')
        links = []
        # Parse links link contents for cited applicable links?
        for line in lines:
            if line.strip() not in links:
                links.append(line.strip())
            else:
                self.debug('Removed ' + line)
        del lines
        for link in links:
            if self.isValidUrl(link):
                self.download(link)
        self.broadcast('COMPLETE')
    
    def isValidUrl(self, url):
        return bool(re.match(r'https?://(www.)?tutsplus\.com/(course|ebook)/.+', url))
    
    def download(self, url):
        if re.match(r'https?://(www.)?tutsplus\.com/course/.+', url):
            self.downloadCourse(url)
        elif re.match(r'https?://(www.)?tutsplus\.com/ebook/.+', url):
            self.downloadEbook(url)
    
    def setEbook(self, ebook_page_url):
        self.HTML['ebook'] = self.session.get(ebook_page_url, verify=True).text
        self.e_soup = BeautifulSoup(self.HTML['ebook'])
        self.TEXT['ebook'] = self.getEbookName()
        self.COURSE_DL_LOCATION = self.DOWNLOAD_LOCATION + '/' + self.formatFilename(self.TEXT['ebook'])
        self.makedirs(self.COURSE_DL_LOCATION)
        self.broadcast('==== NEW EBOOK ====')
        self.broadcast('EBook: "' + self.TEXT['ebook'] + '"')
    
    def getEbookName(self):
        return self.e_soup.find('h2', class_='entry-title').find('span', class_='title-text').get_text(strip=True)
    
    def downloadEbook(self, url=''):
        if url:
            self.setEbook(url)
            self.generateEbookMetaFile()
        filename = self.formatFilename(self.TEXT['ebook'])
        self.broadcast('Downloading ' + filename + ' ...')
        u = self.session.get(self.getEbookLink())
        fileLocation = self.COURSE_DL_LOCATION + '/' + filename + '.zip'
        localFile = open(fileLocation, 'wb')
        localFile.write(u.content)
        localFile.close()
        self.debug('Finished downloading "' + filename + '.zip"')
    
    def getEbookLink(self):
        for link in self.e_soup.find_all('div', class_='ebook-meta-wrap').find_all('a', text=re.compile(r'download ebook', re.IGNORECASE)):
            return link.get('href')
    
    def generateEbookMetaFile(self):
        metafile = open(self.COURSE_DL_LOCATION + '/README.txt', 'w')
        
        title = 'TITLE:      ' + self.TEXT['ebook'] + '\n'
        author = 'AUTHOR:     ' + [text for text in self.e_soup.find('span', class_='title-author').stripped_strings][1] + '\n'
        publisher = 'PUBLISHER:  ' + [text for text in self.e_soup.find('div', class_='post-type-meta').find('strong', text=re.compile(r'Publisher:', re.IGNORECASE)).parent.stripped_strings][1] + '\n'
        pages = 'PAGES:      ' + [text for text in self.e_soup.find('div', class_='post-type-meta').find('strong', text=re.compile(r'Pages:', re.IGNORECASE)).parent.stripped_strings][1] + '\n'
        formats = 'FORMATS:    ' + [text for text in self.e_soup.find('div', class_='post-type-meta').find('strong', text=re.compile(r'Formats:', re.IGNORECASE)).parent.stripped_strings][1] + '\n'
        
        metafile.write(self.unencode(title + author + publisher + pages + formats))
        
        # summary of book from page
        metafile.write('\n\n\n')
        for soup in self.e_soup.find('div', class_='entry-content').find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if re.match(r'<h\d+>', str(soup)):
                # getting header indentation
                header = '=' * int(re.match(r'<h(\d+)>', str(soup)).group(1))
                metafile.write(header + ' ' + self.unencode(soup.get_text(strip=True)) + ' ' + header + '\n\n')
            else:
                metafile.write(self.unencode(soup.get_text(strip=True) + '\n\n'))
        metafile.close()
    
    def unencode(self, line):
        line = line.replace(u'\u2019', "'")
        line = re.sub(r'\\u201[cd]', '"', line)
        return foo
    
    def setCourse(self, course_page_url):
        self.HTML['course'] = self.session.get(course_page_url, verify=True).text
        self.c_soup = BeautifulSoup(self.COURSE_HTML)
        self.TEXT['course'] = self.getCourseName()
        self.broadcast('==== NEW COURSE ====')
        self.broadcast('Course: "' + self.COURSE_TEXT + '".')
        self.COURSE_DL_LOCATION = self.DOWNLOAD_LOCATION + '/' + self.formatFilename(self.TEXT['course'])
        self.makedirs(self.COURSE_DL_LOCATION)
        self.table_of_contents = self.COURSE_DL_LOCATION + '/README.txt'
    
    def downloadCourse(self, course_url=''):
        # Check if download link exists for entire course
        if course_url:
            self.setCourse(course_url)
        links = self.getCourseLessons()
        if self.c_soup.find(id='course-download'):
            url = self.c_soup.find(id='course-download').a.get('href')
            self.downloadCourseFile(url)
        # Loop through each lesson page
        else:
            for count in range(0, len(links)):
                self.setLesson(links[count])
                self.LESSON_NUM = count + 1
                self.downloadLessonFiles()
    
    def __init__(self, dl_location='', username='', password='', session = ''):
        self.USERNAME = username
        self.PASSWORD = password
        self.DOWNLOAD_LOCATION = dl_location
        if not session:
            self.session = requests.session()
            self.login()
        else:
            self.session = session
    
    def login(self):
        login_data = {
            'remember_login': '1',
            'amember_login': self.USERNAME,
            'amember_pass': self.PASSWORD,
        }
        self.debug('Logging in as "' + self.USERNAME + '" ...')
        r = self.session.post('https://tutsplus.com/amember/login.php', verify=True, data=login_data)
        self.debug('Done')
        if not self.isAuthenticated():
            self.broadcast('Unable to login as "' + self.USERNAME + '". Check that the username and password are correct.')
            sys.exit(1)
        else:
            self.broadcast('Logged in as "' + self.USERNAME + '" successfully!')

    def isAuthenticated(self):
        self.debug('Verifying authentication ...')
        login_soup = BeautifulSoup(self.session.get('https://tutsplus.com/amember/login.php', verify=True).text, 'lxml')
        return not login_soup.find('title', text=re.compile(r'please login', re.IGNORECASE))
    
    def print_log(self, message):
        log = open(self.DOWNLOAD_LOCATION + '/TutsPlusDownloader-LOG.txt', 'a')
        log.write(message + '\n')
        log.close()
    
    def debug(self, message):
        self.log(message, 'debug')
    def broadcast(self, message):
        self.log(message, 'broadcast')
    def log(self, message, level='debug'):
        if level == 'debug' and self.REPORTING > 2:
            print message
            self.print_log(message)
        elif level == 'warning' and self.REPORTING > 1:
            print message
            self.print_log(message)
        elif level == 'broadcast':
            print message
            if self.REPORTING > 0:
                self.print_log(message)
    
    def generateTOC(self):
        self.broadcast('Creating table of contents ...')
        toc = open(self.table_of_contents, 'w')
        toc.write(self.TEXT['course'] + '\n')
        for row in self.c_soup.find(id='course-lessons').find_all('tr'):
            if 'section-footer' not in row.get('class'):
                if row.find('a').get('href'):
                    toc.write('      ')
                toc.write(row.find('td', class_='section-title').get_text(strip=True) + ' ...... [' + row.find('td', class_='section-time').get_text(strip=True) + ']')
        toc.close()
        self.debug('Done')
    
    def getCourseLessons(self):
        links = []
        self.broadcast('Collecting links from course page ...')
        for row in self.c_soup.find(id='course-lessons').find_all('tr'):
            # Skip over quizzes
            if not row.find('td', class_='section-time', text=re.compile(r'quiz', re.IGNORECASE)) and 'section-footer' not in row.get('class'):
                # Check if section header
                if row.find('a').get('href'):
                    links.append(row.find('a').get('href'))
        self.debug('Done')
        return links
    
    def setLesson(self, lesson_page_url):
        self.HTML['lesson'] = self.session.get(lesson_page_url, verify=True).text
        self.l_soup = BeautifulSoup(self.LESSON_HTML)
        if self.TEXT['section'] != self.getSectionName():
            self.TEXT['section'] = self.getSectionName()
            self.debug('Section: "' + self.TEXT['section'] + '".')
        self.TEXT['lesson'] = self.getLessonName()
        self.debug('Lesson: "' + self.TEXT['lesson'] + '".')
    
    def getCourseName(self):
        if self.c_soup:
            return self.c_soup.find('h2', 'course-title').find('span', 'title-text').get_text(strip=True)
        elif self.l_soup:
            return self.l_soup.find(id='lesson-breadcrumb').find('li', 'bc-course').get_text(strip=True)
    
    def getSectionName(self):
        return self.l_soup.find(id='lesson-breadcrumb').find('li', 'bc-section').get_text(strip=True)
    
    def getLessonName(self):
        return self.l_soup.find(id='lesson-breadcrumb').find('li', 'bc-title').get_text(strip=True)
    
    def isQuiz(self):
        return self.l_soup.find('div', 'lesson-meta-wrap').find_all('a', text=re.compile('take quiz', re.IGNORECASE))
    
    def downloadCourseFile(self, url):
        filename = self.formatFilename(self.TEXT['course'])
        self.broadcast('Downloading ' + filename + '  ...')
        u = self.session.get(url, allow_redirects=True)
        fileLocation = self.COURSE_DL_LOCATION + '/' + filename + '.zip'
        localFile = open(fileLocation, 'wb')
        localFile.write(u.content)
        localFile.close()
        self.debug('Finished downloading "' + filename + '.zip"')
    
    def downloadLessonFiles(self):
        if self.l_soup.find(id='logged-out-lesson'):
            self.login()
        if not self.isQuiz():
            self.makedirs(self.COURSE_DL_LOCATION + '/' + self.formatFilename(self.TEXT['section']) + '/')
            self.downloadProjectFiles()
            self.downloadVideo()
    
    def downloadProjectFiles(self):
        url = ''
        for link in self.l_soup.find('div', 'lesson-meta-wrap').find_all('a', text=re.compile('download project files', re.IGNORECASE)):
            url = link.get('href')
        if url:
            self.downloadFile(url)
    
    def downloadVideo(self):
        url = ''
        for link in self.l_soup.find('div', 'lesson-meta-wrap').find_all('a', text=re.compile('download video', re.IGNORECASE)):
            url = link.get('href')
        self.downloadFile(url)
    
    def downloadFile(self, url, fileLocation='', name_format = '', ext = ''):
        u = self.session.get(url, allow_redirects=True)
        if not name_format:
            filename = self.formatFilename('%02d - %s' % (self.LESSON_NUM, self.TEXT['lesson']))
        else:
            filename = self.formatFilename(name_format)
        
        self.broadcast('Downloading ' + filename + ' ...')
        
        if not fileLocation:
            fileLocation = self.COURSE_DL_LOCATION + '/' + self.formatFilename(self.TEXT['section'])
        fileLocation = fileLocation + '/' + filename
        localFile = open(fileLocation, 'wb')
        localFile.write(u.content)
        localFile.close()
        filetype = u.headers.get('content-type')
        if not ext:
            if filetype == 'application/zip':
                ext = '.zip'
            elif filetype == 'video/quicktime':
                ext = '.mov'
            elif filetype == 'video/mp4':
                ext = '.mp4'
        os.rename(fileLocation, '%s%s' % (fileLocation, ext))
        self.debug('Renamed "' + filename + '" to "' + filename + ext + '"')
        del u, filetype, localFile, section, course
        self.broadcast('Finished downloading "' + filename + ext + '"')
    
    def getFilename(self, url, name=''):
        reg = re.search(r'\s*filename=[\'"](.*)[\'"]', self.session.get(url).headers.get('content-disposition'))
        if not name:
            if reg:
                name = name.group(1)
            else:
                name = '%02d - %s' % (self.LESSON_NUM, self.TEXT['lesson'])
        return name
    
    def formatFilename(self, filename):
        chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
        return ''.join(c for c in filename if c in chars)
    
    def makedirs(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
