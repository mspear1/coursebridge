from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

# @authors: Ashley, Emily, Louisa, Madelynn

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import helper 
import random
import bcrypt
from datetime import datetime
from datetime import timedelta


import sys, os, random
import imghdr

app.config['UPLOADS'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2*1024*1024 # 2 MB

# # To increase session time 
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


app.secret_key = 'your secret here'
# replace that with a random key

'''app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])'''

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    '''
    This renders to login page for users to sign in when they load the website 
    '''
    # When index is retrieved, automatically check for old posts in the database
    conn = dbi.connect()
    helper.close_old_posts(conn)

    # In case user never clicked 'logged out', but the page is on login.
    # Using individual if statements instead of a for-loop because
    # the logged_in changes the session dictionary size.
    if 'username' in session:
        session.pop('username')
    if 'name' in session:
        session.pop('name')
    if 'id' in session:
        session.pop('id')
    if 'logged_in' in session:
        session.pop('logged_in')
   
    return render_template('login.html',title='Login Page')

@app.route('/main/')
def main():
    '''
    This is the welcome page 
    '''
    return render_template('main.html',title='Welcome Page')


@app.route('/stream/', methods=['GET', 'POST'])
def stream():
    '''
    This handler function gets posts to display for 'get', and for 'post' it 
    filters the posts first with the indicated filters before returning them
    '''
    conn = dbi.connect()
    type = ''
    major = ''
    date_order = ''
    search_query = ''

    if request.method == 'GET':
        posts = helper.get_posts(conn)     
    if request.method == 'POST':
        search_query = request.form.get('search_query')

        # Fetch posts based on the search query
        if search_query is not None:
            search_results = helper.search(conn, search_query)
        else:
            search_results = []

        # Fetch posts based on filters
        type = request.form.get('type')
        major = request.form.get('major')
        if type or major:
            filtered = helper.filter_posts(conn, type, major)
        else:
            filtered = helper.get_posts(conn)

        # Combine such that only posts *both* the search and filter grabbed will be displayed
        posts = []
        if len(search_results) > 0:
            for i in filtered:
                if i in search_results: # if common, add to posts to stream
                    posts.append(i)

        date_order = request.form.get('dateorder')

        # sort posts by date order
        if date_order == 'early':
            posts = sorted(posts, key=lambda x:x['date'])
        elif date_order == 'late':
            posts = sorted(posts, key=lambda x:x['date'], reverse=True)
        
        # To let the user know that posts have been filtered
        flash('Filters have been applied') 

    # reformatting for display purposes and slicing for database purposes
    for post in posts:
        if post['timestamp']:   
            post['timestamp'] = get_time_difference(post['timestamp'])
        if post['major']:
            post['major'] = post['major'].replace('_', ' ')
        post['tag'] = post['tag'].replace('_', ' ')
        if post['major2_minor']:
            post['major2_minor'] = post['major2_minor'].replace('_', ' ')
        if len(post['description']) > 100: # If the description is too long, cut it short
            post['description'] = post['description'][:100] + '...'

    majors_list = [[i,i.replace("_"," ")] for i in helper.get_majors()]
        
    return render_template('stream.html', 
                            title='Stream - Coursebridge', posts = posts, majors=majors_list, type=type,
                            major=major, date_order=date_order, search=search_query)


def get_time_difference(timestamp):
    '''
    inputs: timestamp
    Helper function to convert the timestamp into a time format that is more
    digestible to users (e.g., Wednesday, 11/15)
    '''
    current_time = datetime.now()
    time_difference = current_time - timestamp

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days} {'day' if days == 1 else 'days'} ago"
    elif hours > 0:
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    else:
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    
@app.route('/create/', methods=['GET', 'POST'])
def create_post():
    '''
    Method for creating the post; calls helper.add() to insert a new post, get and post
    '''

    if request.method == 'GET':
        return render_template('create_post.html', title='Create Post - Coursebridge')
    else:
        conn = dbi.connect()

        form_info = request.form  # dictionary of form data

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Handling the case where the session expired somehow
        if 'id' in session:
            id = session['id']

            helper.add_post(conn, form_info, timestamp, id)
            flash('Your post is created!')
        else:
            flash('Sorry, your session has expired. Please login again.')
            redirect(url_for('login'))
        
        return redirect(url_for('stream')) # redirect to the stream page so users can view others' posts

@app.route('/createprofile/', methods=["GET", "POST"])
def create_profile():
    '''
    Method for creating the user's profile
    Renders the profile form for GET, 
    inserts the form information into database for POST
    '''
    if request.method == 'GET':
        majors_list = [[i,i.replace("_"," ")] for i in helper.get_majors()]

        return render_template('profile_form.html', title="Create Profile - Coursebridge", majors=majors_list)
    else:
        try:
            id = int(session['id'])
            f = request.files['pic']
            user_filename = f.filename
            if user_filename: # If the user uploaded a picture
                ext = user_filename.split('.')[-1]
                filename = secure_filename('{}.{}'.format(id,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                f.save(pathname)
            conn = dbi.connect()

            name = request.form['name']
            phnumber = request.form['phonenum']
            major1 = request.form['major1']
            major2_minor = request.form['major2_minor']
            dorm = request.form['dorm']
            
            if f: 
                helper.upload_profile_pic(conn, id, filename)

            helper.add_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id)
            # To get name to display on nav bar after creating a profile
            user_name = helper.get_user_info(conn, id)['name']
            session['name'] = user_name

            # To get phone_num to display
            session['phone_num'] = phnumber
            flash('Profile Created!')
           
            # Bring first-time users to the welcome/main page
            return redirect(url_for('main'))
        
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return render_template('profile_form.html',src='',nm='')
        


@app.route('/updateprofile/<id>', methods=["GET", "POST"])
def update_profile(id):
    '''
    Method for updating the user's profile
    Renders the profile form for GET, 
    inserts the form information into database for POST
    '''
    conn = dbi.connect()
    id = int(id)

    if request.method == 'GET':
        majors_list = [[i,i.replace("_"," ")] for i in helper.get_majors()]

        user_info = helper.get_user_info(conn, id)

        return render_template('update_profile_form.html', title="Update Profile - Coursebridge", 
                                majors=majors_list, user=user_info, id=id)
    else:
        try:
            id = int(session['id'])
            f = request.files['pic']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            filename = secure_filename('{}.{}'.format(id,ext))
            pathname = os.path.join(app.config['UPLOADS'],filename)
            f.save(pathname)
            conn = dbi.connect()

            name = request.form['name']
            phnumber = request.form['phonenum']
            major1 = request.form['major1']
            major2_minor = request.form['major2_minor']
            dorm = request.form['dorm']

            # Handling the case where the session expires while the user
            # is in the midst of creating a profile
            if 'id' in session:
                # upload file if it exists
                if f: 
                    helper.upload_profile_pic(conn, id, filename)

                helper.update_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id)
                # To get name to display on nav bar after creating a profile
                user_name = helper.get_user_info(conn, id)['name']
                session['name'] = user_name

                # To get phone_num to display
                session['phone_num'] = phnumber
                flash('Profile Updated!')
            else:
                flash('Sorry, your session has expired. Please login again.')
                redirect(url_for('login'))

            return redirect(url_for('profile', id=id))
        
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return render_template('profile_form.html',src='',nm='')
   
@app.route('/display/<pid>', methods=["GET", "POST"])  # may not need post
def display_post(pid):
    '''
    Inputs: pid, the post ID
    Method for displaying a singular full post
    Can also post a comment for the post
    '''
    conn = dbi.connect()
    id = int(session['id'])

    if request.method == 'GET':
        post = helper.get_postinfo(conn, pid)

        # Reformatting data for display purposes
        if post['timestamp']:   
            post['timestamp'] = get_time_difference(post['timestamp'])
        if post['major']:
            post['major'] = post['major'].replace('_', ' ')
        post['tag'] = post['tag'].replace('_', ' ')
        if post['major2_minor']:
            post['major2_minor'] = post['major2_minor'].replace('_', ' ')
        comments = helper.get_post_comments(conn, pid)
        for comment in comments:
            comment['timestamp'] = get_time_difference(comment['timestamp'])
        
        sid = helper.get_poster_sid(conn, pid)['sid']
        # Check if the phone number is already requested
        phnum_req = helper.check_request_ph(conn, id, sid)
        
        return render_template('display_post.html', title='Display Post - Coursebridge', 
                        post=post, pid=pid, comments=comments, phnum_request=phnum_req)
        
    else: # Post request for commenting
        new_comment = request.form.get("comment")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M") # Get current time
        helper.insert_comment(conn, new_comment, id, timestamp, pid)

        # Return back to the page after inserting the comment
        return redirect(url_for('display_post', pid=pid)) 


@app.route('/phrequest/<pid>', methods=['GET'])
def request_ph(pid):
    '''
    Inputs: pid, the post ID
    Method for handling the phone number request
    '''
    conn = dbi.connect()
    sid = helper.get_poster_sid(conn, pid)['sid']
    id = int(session['id'])
    helper.make_phone_request(conn, sid, id) 
    return redirect(url_for('display_post', pid=pid))


@app.route('/update/<pid>', methods=["GET", "POST"])
def update_post(pid):
    '''
    Inputs: pid, postId
    Method for getting the update post page and also updating the post
    '''
    conn = dbi.connect()
    if request.method == 'GET':
        post = helper.get_postinfo(conn, pid)
        post['date'] = post['date'].strftime("%m-%d-%Y") # To prefill accurately

        return render_template('update_post.html', title='Update Post - Coursebridge', post=post, pid=pid)
    else:
        conn = dbi.connect()
        action = request.form.get('submit')
        if action == 'update':
            form_info = request.form  # dictionary of form data
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Handling the case where the session expires while the user
            # is in the midst of creating a post
            id = 0
            if 'id' in session:
                id = session['id']

                # To get name to display
                name = helper.get_user_info(conn, id)['name']
                session['name'] = name   
            else:
                flash('Sorry, your session has expired. Please login again.')
                redirect(url_for('login'))
            
            helper.update_post(conn, form_info, timestamp, pid)

            flash('Your post is updated!')
        elif action == 'delete': # for deleting the post
            helper.delete_post(conn, pid)
            flash('Post was permanently deleted successfully')
        else:
            helper.close_post(conn, pid)
            flash('Post was closed successfully. You can view your closed posts on your profile.')
        return redirect(url_for('stream')) # redirect to the stream page so users can view others' posts

@app.route('/logout')
def logout():
    '''
    Function that checks the current status and logs out the user
    if they were logged in. 
    '''
    if 'username' in session:
        #username = session['username']
        session.pop('username')
        if 'name' in session:
            session.pop('name')
        if 'id' in session:
            session.pop('id')
        if 'logged_in' in session:
            session.pop('logged_in')
        flash('You are logged out')
        return redirect(url_for('index'))
    else:
        flash('You are not logged in. Please login or signup')
        return redirect(url_for('index') )

@app.route('/join/', methods=["POST", "GET"])
def join():
    '''
    Allows new users to sign up for an account with email and password, 
    encrypted with bycrpt. 
    '''
    if request.method == 'GET':
        return render_template('join.html', title="Join Coursebridge")
    
    # For form post from join
    username = request.form.get('username')
    session['username'] = username
    passwd1 = request.form.get('password1')
    passwd2 = request.form.get('password2')

    # Verifies that the email is @wellesley.edu
    if not username.endswith('@wellesley.edu'):
        flash('Please enter a valid @wellesley.edu email address.')
        return redirect(url_for('join'))

    # Verifies that password1 and password2 match 
    if passwd1 != passwd2:
        flash('passwords do not match')
        return redirect( url_for('index'))
    hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                           bcrypt.gensalt())
    stored = hashed.decode('utf-8')
    print(passwd1, type(passwd1), hashed, stored)
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''INSERT INTO student(id,email_address,hashed)
                        VALUES(null,%s,%s)''',
                        [username, stored])
        conn.commit()
    except Exception as err:
        # flash('That username is taken: {}'.format(repr(err)))
        flash("An account already exists with this email. Please login :)")
        return redirect(url_for('index'))
    curs.execute('select last_insert_id()')
    row = curs.fetchone()
    id = row[0]
    # flash('FYI, you were issued ID {}'.format(id))
    flash('You successfully created an account with {}'.format(username))
    session['username'] = username
    session['id'] = id
    session['logged_in'] = True
    session['visits'] = 1
    # return redirect( url_for('user', username=username) )
    return redirect( url_for('create_profile') )  # redirect to creating profile after joining

@app.route('/login/', methods=["POST", "GET"])
def login():
    '''
    Gets the login for for user
    Logs in the user using a post method 
    '''
    # Gets the form for user to login 
    if request.method == 'GET':
        return render_template('login.html', title="Login to Coursebridge")
    
    # Posts the form once user fills out information 
    else:
        username = request.form.get('username')
        passwd = request.form.get('password')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''SELECT id,hashed
                        FROM student
                        WHERE email_address = %s''',
                    [username])
        row = curs.fetchone()
        if row is None:
            # Same response as wrong password,
            # so no information about what went wrong
            flash('Login incorrect. Try again or join')
            return redirect( url_for('index'))
        stored = row['hashed']
        print('database has stored: {} {}'.format(stored,type(stored)))
        print('form supplied passwd: {} {}'.format(passwd,type(passwd)))
        hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),
                                stored.encode('utf-8'))
        hashed2_str = hashed2.decode('utf-8')
        print('rehash is: {} {}'.format(hashed2_str,type(hashed2_str)))

        if hashed2_str == stored:
            print('they match!')
            flash('successfully logged in with '+username)
            session['username'] = username
            session['id'] = row['id']
            session['logged_in'] = True
            session['visits'] = 1
           
            # To get name to display
            name = helper.get_user_info(conn, row['id'])['name']
            if name:
                session['name'] = name
                # return redirect( url_for('user', username=username) )
                return redirect( url_for('stream') )
            
            # In case they created an account before but 
            # didn't actually create their profile (exited the tab) 
            else: 
                return redirect(url_for('create_profile'))

        else:
            flash('login incorrect. Try again or join')
            return redirect( url_for('index'))


@app.route('/profile/<id>', methods=['GET', 'POST']) 
def profile(id):
    """
    Input: user id 
    Displays user profile along with the information they put in 
    when they created the profile. 
    """
    conn = dbi.connect()
    id = int(id)
    if request.method == 'GET':
        user_info = helper.get_user_info(conn, id)
        phnum_requests_received = helper.get_phone_requests_received(conn, id)

        # deletes the underscores when displaying majors 
        if user_info['major1']: 
            user_info["major1"] = user_info['major1'].replace('_', ' ')
        
        if user_info['major2_minor']: 
            user_info["major2_minor"] = user_info['major2_minor'].replace('_', ' ')
            
        for item in phnum_requests_received:
            item['major1'] = item['major1'].replace('_', ' ')
        phnum_requests_made = helper.get_phone_requests_made(conn, id)
        for item in phnum_requests_made:
            item['major1'] = item['major1'].replace('_', ' ')

        posts = helper.get_user_posts(conn, id)
        posts = sorted(posts, key=lambda x:x['date']) # sort early-oldest

        for post in posts:
            if post['timestamp']:   
                post['timestamp'] = get_time_difference(post['timestamp'])
            if post['major']:
                post['major'] = post['major'].replace('_', ' ')
            post['tag'] = post['tag'].replace('_', ' ')
            if post['major2_minor']:
                post['major2_minor'] = post['major2_minor'].replace('_', ' ')
            if len(post['description']) > 100: # If the description is too long, cut it short
                post['description'] = post['description'][:100] + '...'
        return render_template('profile.html', user_info = user_info, 
                                title="Profile - Coursebridge", phnum_requests_received=phnum_requests_received,
                                phnum_requests_made=phnum_requests_made, id=id, posts=posts)
    else:
        if request.form.get('delete'):
            pid = request.form.get('delete')
            helper.delete_post(conn, pid)
            flash('Post was permanently deleted successfully')
        elif request.form.get('archive'):
            pid = request.form.get('archive')
            helper.close_post(conn, pid)
            flash('Post was closed successfully. You can view your closed posts on your profile.')
        else:
            sid = request.form['phnum_sid']
            helper.accept_phone_req(conn, id, sid) 
        return redirect(url_for('profile', id=id))

@app.route('/accounts/')
def accounts():
    """
    Displays a list of all users, including their profile picture, 
    email address, majors, and a link to their profile. 
    """ 
    conn = dbi.connect()
    accounts = helper.get_accounts(conn)

    # deletes the underscores when displaying majors 
    for account in accounts: 
        if account["major1"]: 
            account["major1"] = account['major1'].replace('_', ' ')
        if account["major2_minor"]:
            account["major2_minor"] = account['major2_minor'].replace('_', ' ')

    return render_template('accounts.html', title="Accounts", all_users = accounts)

@app.route('/update_comment/<cid>', methods=["GET", "POST"])  # may not need post
def update_comment(cid):
    conn = dbi.connect()
    id = int(session['id'])
    cid_post_id = helper.get_post_id_given_cid(conn, cid)['pid']
    if request.method == 'GET': 
        comment = helper.get_comment_given_cid(conn, cid)['description']
        
        return render_template('update_comment.html', title="Update Comment", cid=cid, comment=comment, pid=cid_post_id)
    else:
        # pid = request.form.get('update') # Unsure, but one way to get the pid, since we have to pass in cid through the url
        action = request.form.get('submit')
        comment = request.form.get('comment')
        if action == 'update':
            # pid = request.form.get('update')
            helper.update_comment(conn, cid, comment)
        else: # action is delete
            # pid = request.form.get('delete')
            helper.delete_comment(conn, cid)
        return redirect(url_for('display_post', pid=cid_post_id))

# May not include           
# @app.route('/delete_comment/<cid>', methods=["POST"])
# def delete_comment(cid):
#     conn = dbi.connect()
#     helper.delete_comment(conn, cid)
#     cid_post_id = helper.get_post_id_given_cid(conn, cid)['pid']
#     return redirect(url_for('display_post', pid=cid_post_id))

# # yet to implement
# @app.route('/deleteorclose/<pid>')
# def delete_or_close(pid):
#     conn = dbi.connect()
#     action = request.form.get('submit')
#     if action == 'delete': # for deleting the post
#         helper.delete_post(conn, pid)
#         flash('Post was permanently deleted successfully')
#     else:
#         helper.close_post(conn, pid)


if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'coursebridge_db' 
    print('will connect to {}'.format(db_to_use))
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0', port)
