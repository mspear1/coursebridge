from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import helper 
import random
from datetime import datetime

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    return render_template('main.html',title='Hello')

@app.route('/stream/')
def stream():
    return render_template('stream.html',
                           title='Stream - Coursebridge')

@app.route('/create/', methods=['GET', 'POST'])
def create_post():
    '''
    Method for creating the post; calls helper.add to insert a new post
    '''
    # return render_template('create_post.html',
    #                        title='Create Post - Coursebridge')

    if request.method == 'GET':
        return render_template('create_post.html', title='Create Post - Coursebridge')
    else:
        conn = dbi.connect()

        # check if the form should parse the stuff or should get as dictionary
        form_info = request.form  # dictionary of form data
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Things to add:
        # Post needs to refer to session or something to get the actual sid instead of manual input
        #sid = request.form.get('sid')
        # helper.add_post(conn, title, description, timestamp, location, tag, professor, course, None)
        helper.add_post(conn, form_info, timestamp)

        flash('Your post is created!')
        return redirect(url_for('stream')) # redirect to the stream page so users can view others' posts

@app.route('/update/')
def update_post():
    '''
    Method for updating the post
    '''
    pass

# You will probably not need the routes below, but they are here
# just in case. Please delete them if you are not using them

@app.route('/greet/', methods=["GET", "POST"])
def greet():
    if request.method == 'GET':
        return render_template('greet.html', title='Customized Greeting')
    else:
        try:
            username = request.form['username'] # throws error if there's trouble
            flash('form submission successful')
            return render_template('greet.html',
                                   title='Welcome '+username,
                                   name=username)

        except Exception as err:
            flash('form submission error'+str(err))
            return redirect( url_for('index') )

@app.route('/formecho/', methods=['GET','POST'])
def formecho():
    if request.method == 'GET':
        return render_template('form_data.html',
                               method=request.method,
                               form_data=request.args)
    elif request.method == 'POST':
        return render_template('form_data.html',
                               method=request.method,
                               form_data=request.form)
    else:
        # maybe PUT?
        return render_template('form_data.html',
                               method=request.method,
                               form_data={})

@app.route('/testform/')
def testform():
    # these forms go to the formecho route
    return render_template('testform.html')


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
    app.run('0.0.0.0',port)
