import cs304dbi as dbi

# ==========================================================
# The functions that execute queries.
# These functions are called in app.py.

def add_post(conn, form, time):
    ''' Adds a new post to the database and commit
    '''
    title = form['title']
    description = form['description']
    location = form['location']
    tag = form['tag']
    professor = form.get('professor', None) # default is None
    course = form.get('class', None)
    date = form.get('date', None)   # need to fix after fixing calendar date selection
    # timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S') if date else None
    curs = dbi.dict_cursor(conn)
    # need to later add sid
    curs.execute('''insert into post(title, description, timestamp, location, 
                 tag, professor, class, date, status) 
                 values (%s, %s, %s, %s, %s, %s, %s, %s, %s);''', 
                 [title, description, time, location, tag, 
                  professor, course, None, 'open']) # later replace None with functional date
    conn.commit()
    
