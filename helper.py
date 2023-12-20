# @authors: Ashley, Emily, Louisa, Madelynn
import cs304dbi as dbi
from datetime import datetime, timedelta

# ==========================================================
# This file is to hold functions that execute queries.
# These functions are called in app.py.

def validate(form):
    '''
    Input: Post form
    Helper function for shortening form entries as needed
    '''
    title = form['title']
    if title and len(title) > 30:
        title = title[:30]
    description = form['description']
    if description and len(description) > 500:
        description = description[:500]
    location = form['location']
    if location and len(location) > 50:
        location = location[:50]
    oncampus = form['oncampus']
    tag = form['tag']
    professor = form.get('professor', None) # default is None
    if professor and len(professor) > 50:
        professor = professor[:50]
    course = form.get('class', None)
    if course and len(course) > 8:
        course = course[:8]
    date = form.get('date')  
    date = datetime.strptime(date, '%m-%d-%Y') # re-formatted the date so sql will accept it
    return title, description, location, oncampus, tag, professor, course, date


def add_post(conn, form, time, sid):
    ''' 
    Inputs: form, timestamp, and student id
    Adds a new post to the database and commits
    '''
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the web interface
    title, description, location, oncampus, tag, professor, course, date = validate(form)
    curs = dbi.dict_cursor(conn)

    curs.execute('''insert into post(title, description, timestamp, location, 
                    on_campus, tag, professor, class, date, status, sid) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''', 
                    [title, description, time, location, oncampus, tag, 
                    professor, course, date, 'open', sid]) 
    conn.commit()

def update_post(conn, form, time, pid):
    ''' 
    Inputs: post form content, timestamp, post id
    Updates a post in the database and commits
    ''' 
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the web interface
    title, description, location, oncampus, tag, professor, course, date = validate(form)

    curs = dbi.dict_cursor(conn)
    
    curs.execute('''update post set title = %s, description = %s, location = %s, 
                    on_campus = %s, tag = %s, professor = %s, class = %s, 
                    date = %s, status = %s where pid = %s''', 
                    [title, description, location, oncampus, tag, 
                    professor, course, date, 'open', pid]) 
    conn.commit()

def delete_post(conn, pid):
    '''
    Inputs: pid, id of post
    Deletes post from the database and commit
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''delete from post where pid = %s''', [pid])
    conn.commit()

def close_post(conn, pid):
    '''
    Inputs: pid, id of post
    Closes the post, which means it won't show up on the stream
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''update post set status = 'closed'
                    where post.pid = %s''', [pid])
    conn.commit()
    



def get_postinfo(conn, pid):
    '''
    Inputs: post id 
    Retrieve the post information given the pid and return as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, 
                    title, description, timestamp, location, on_campus, tag, 
                    professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id and pid = %s''', [pid])
    result = curs.fetchone()
    return result
    
def get_posts(conn):
    '''
    Retrieves posts with information for the stream page and returns them as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, title, description, 
                    timestamp, location, on_campus, tag, professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id and post.status = 'open';''')
    return curs.fetchall()

def get_user_posts(conn, student_ID):
    '''
    Inputs: student id
    Retrieves posts for a specific user's account page and returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, title, description, 
                    timestamp, location, on_campus, tag, professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id and student.id = %s;'''
                    , [student_ID])
    return curs.fetchall()


def filter_posts(conn, type, major, search_query):
    '''
    Inputs: type of post, major, search query
    Filters posts based on criteron and keywords and returns the filtered ones as a dictionary
    '''
    curs = dbi.dict_cursor(conn)

    query = '''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, title, description, 
                    timestamp, location, on_campus, tag, professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id'''
    placeholders = []

    if type:
        query += ''' and tag = %s'''
        placeholders.append(type)
    if major:
        query += ''' and (student.major1 = %s or student.major2_minor = %s)'''
        placeholders.append(major)
        placeholders.append(major)
    if search_query:
        # split query into separate words to search mentions
        search = ['%' + i + '%' for i in search_query.split()]
        for i in search:
            # check within title and description for each item
            query += ''' and (title LIKE %s OR description LIKE %s) ''' 

        # make each item appear 2 times for each %s placeholder
        for i in search:
            placeholders.append(i)
            placeholders.append(i)

    
    query += ''';'''

    curs.execute(query, placeholders)
    return curs.fetchall()

def search_accounts(conn, search_query):
    '''
    Inputs: search_query
    Searches through users, filters out ones without mentioned keywords
    '''
    # split query into separate words to search mentions
    search = ['%' + i + '%' for i in search_query.split()]

    curs = dbi.dict_cursor(conn)
    sql_query = '''select id, name, email_address, major1, major2_minor, 
                    profile_pic, dorm_hall from student where '''
    for i in search:
        # check within title and description for each item
        sql_query += '''(name LIKE %s OR major1 LIKE %s OR major2_minor LIKE %s OR email_address LIKE %s or dorm_hall like %s) and '''
    
    sql_query = sql_query[:-4] + ''';''' # remove last "and", add semicolon

    # make each item appear 2 times for each %s placeholder
    placeholders = []
    for i in search:
        for j in range(5):
            placeholders.append(i)
    curs.execute(sql_query, placeholders)

    return curs.fetchall()


def upload_profile_pic(conn, nm, filename):
    '''
    Uploads the user's profile picture to the database
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into student(id,profile_pic) values (%s,%s)
                    on duplicate key update profile_pic = %s''',
                    [nm, filename, filename])
    conn.commit()

def add_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id):
    '''
    Inputs: name, phnumber, major1, major2_minor, dorm, id of user
    Adds the user's profile information to the database
    '''
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the browser
    if name and len(name) > 40:
        name = name[:40]
    if phnumber and len(phnumber) > 12:
        phnumber= phnumber[:12]
    if dorm and len(dorm) > 20:
        dorm = dorm[:20]
    curs = dbi.dict_cursor(conn)
    
    curs.execute('''update student set name = %s, phone_num = %s, major1 = %s, 
                    major2_minor = %s, dorm_hall = %s where id = %s''', 
                    [name, phnumber, major1, major2_minor, dorm, id])
    conn.commit()

def update_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id):
    '''
    Inputs: name, phnumber, major1, major2_minor, dorm, id of user
    Updates the user's profile information in the database
    '''
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the browser
    if name and len(name) > 40:
        name = name[:40]
    if phnumber and len(phnumber) > 12:
        phnumber= phnumber[:12]
    if dorm and len(dorm) > 20:
        dorm = dorm[:20]
    curs = dbi.dict_cursor(conn)
    
    curs.execute('''update student set name = %s, phone_num = %s, major1 = %s, 
                    major2_minor = %s, dorm_hall = %s where id = %s''', 
                    [name, phnumber, major1, major2_minor, dorm, id])
    conn.commit()

def get_user_info(conn, id):
    '''
    Input: user's id
    Gets the user's information given the id and returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select name, phone_num, email_address, major1, 
                    major2_minor, dorm_hall, profile_pic 
                    from student where id = %s''', [id])
    return curs.fetchone()

def get_post_comments(conn, postid):
    '''
    Inputs: The postid (pid)
    Gets the comments for a post given the postid and returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select cid, description, sid, timestamp, pid,
                    name 
                    from comment, student where 
                    pid = %s and comment.sid = student.id;''', 
                    [postid])
    return curs.fetchall()

def get_poster_sid(conn, pid):
    '''
    Inputs: post id (pid)
    Gets the original poster's sid, for making a phone request, 
    returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select sid from post
                    where post.pid = %s''',
                    [pid])
    return curs.fetchone()
    

def insert_comment(conn, comment, sid, time, pid):
    '''
    Inputs: comment, student id (sid) of commenter, timestamp, post id (pid)
    Inserts the user comment into the database and commits
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into comment(description, sid, timestamp, pid)
                    values (%s, %s, %s, %s)''',
                    [comment, sid, time, pid])
    conn.commit()

def update_comment(conn, cid, comment):
    '''
    Inputs: comment id (cid), comment
    Updates the user comment and commits
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''update comment set description = %s
                    where cid=%s''',
                    [comment, cid])
    conn.commit()

def delete_comment(conn, cid):
    '''
    Inputs: comment id (cid), comment
    Deletes the user comment and commits
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''delete from comment
                    where cid=%s''',
                    [cid])
    conn.commit()

def make_phone_request(conn, sid, id):
    '''
    Inputs: student id of approver, id of requester 
    Inserts phone request into the database
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into phnum(requester, approver, approved)
                    values (%s, %s, %s)''',
                    [id, sid, 'no'])
    conn.commit()

def check_request_ph(conn, id, sid):
    '''
    Inputs: id of requester, id of approver 
    Checks if the user already requested the poster's phone number,
    returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from phnum where
                    requester=%s and approver=%s''',
                    [id, sid])
    return curs.fetchall()

def get_accounts(conn):
    '''
    Gets all users' accounts with information such as 
    id, name, email_address, major1, major2/minor, profile pics, and dorms,
    returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select id, name, email_address, major1, major2_minor, 
                    profile_pic, dorm_hall from student''') 
    return curs.fetchall()

def get_phone_requests_received(conn, id):
    '''
    Inputs: id of user
    Gets all the phone number requests that the user received along with requester info,
    returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select requester, approver, approved,
                    student.name as name, student.major1 as major1
                    from phnum, student 
                    where approver=%s and phnum.requester = student.id''', [id])
    return curs.fetchall()

def get_phone_requests_made(conn, id):
    '''
    Inputs: id of user
    Gets all the phone number requests that the user made along with approver info,
    returns as a dictionary
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select requester, approver, approved,
                    student.name as name, student.major1 as major1, student.phone_num as phone
                    from phnum, student 
                    where requester=%s and phnum.approver = student.id''', [id])
    return curs.fetchall()

def accept_phone_req(conn, id, sid):
    ''''
    Inputs: id of approver, sid of requester
    Changes approved status to 'yes'
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''update phnum set approved = %s
                    where approver=%s and requester=%s''',
                    ['yes', id, sid])
    conn.commit()

def get_majors():
    '''
    Gets a list of all the majors for dropdowns used throughout html files
    '''
    majors = ['Undecided', 'Africana_Studies', 'American_Studies', 'Anthropology', 'Art', 'Astronomy', 
              'Biological_Sciences', 'Chemistry', 'Classical_Civilization', 'Classical_Studies', 
              'Cognitive_and_Linguistic_Science', 'Computer_Science', 'East_Asian_Languages_and_Cultures',
              'Economics', 'Education', 'English_and_Creative_Writing', 'Environmental_Studies', 
              'French_and_Francophone_Studies', 'Geosciences', 'German_Studies', 'History', 'Italian_Studies', 
              'Language_Studies_Linguistics', 'Mathematics', 'Music', 'Neuroscience', 'Philosophy', 'Physics', 
              'Political_Science', 'Psychology', 'Religion', 'Russian', 'Sociology', 'Spanish_and_Portuguese', 
              'Womens_and_Gender_Studies', 'Other']

    return majors


def close_old_posts(conn):
    #current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Since this isn't an active site, want to keep many posts on, so
    # setting cutoff date to 40 days ago for now
    cutoff_time = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d %H:%M")

    curs = dbi.dict_cursor(conn)
    curs.execute('''UPDATE post SET status = 'closed' WHERE timestamp < %s''', 
                    [cutoff_time])
    conn.commit()

def get_comment_given_cid(conn, cid):
    '''
    Input: cid, the comment id
    Return the comment content given the cid
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select description from comment where cid=%s''',
                    [cid])
    return curs.fetchone()

# May not keep
def get_post_id_given_cid(conn, cid):
    '''
    Get the post id given cid, this function is to help 
    redirect to the post after deleting a comment
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select pid from comment where cid = %s''',
                    [cid])
    return curs.fetchone()


