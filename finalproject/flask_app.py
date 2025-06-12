
from flask import Flask, request, redirect, render_template, session, make_response
from flask_session import Session
from datetime import datetime

import boto3
import uuid

AWSKEY = 'AKIAU6GDZFPYFRYTP2YJ'
AWSSECRET = '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'
PUBLIC_BUCKET = 'azheng-web-public'
STORAGE_URL = 'https://azheng-web-public.s3.us-east-2.amazonaws.com/'


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False # session cookie will be shut down when web closed
app.config["SESSION_TYPE"] = "filesystem" # data will be stored in server
Session(app)

def get_date(blog):
    return blog['date']


# Helper function to get a dynamodb table
def get_table(name):
    client = boto3.resource(service_name='dynamodb',
                        region_name='us-east-2',
                        aws_access_key_id=AWSKEY,
                        aws_secret_access_key=AWSSECRET)
    table = client.Table(name)
    return table

def get_public_bucket():
    s3 = boto3.resource(service_name='s3', region_name='us-east-2',
                        aws_access_key_id=AWSKEY,
                        aws_secret_access_key=AWSSECRET)
    bucket = s3.Bucket(PUBLIC_BUCKET)
    return bucket


#login
@app.route('/')
def home():
    return render_template("login.html") # render login.html

@app.route('/thing')
def thing():
    return session["thing"]

@app.route('/login') #check account existed
def login():
    email = request.args.get("email")
    password = request.args.get("password")

    table = get_table("Users")
    item = table.get_item(Key={"email": email})

    if 'Item' not in item:
        return {'result': 'Email not found. Please, sign up first'}

    user = item['Item']

    if password != user['password']:
        return {'result': 'Password does not match.'}

    session["email"] = user["email"]
    session["username"] = user.get("username")

    result = {'result': 'OK'}
    response = make_response(result)
    return response


#signin.html

@app.route('/signin')
def signin():
    email = request.args.get("email")
    password = request.args.get("password")
    username = request.args.get("username")

    table = get_table("Users")
    item = table.get_item(Key={"email": email})

    if 'Item' in item:
        return {'result': 'email exists'}
    elif '@' not in email or '.' not in email:
        return {'result': 'Email must include "@" and ".", please try again'}

    response = table.scan(
        FilterExpression="username = :username",
        ExpressionAttributeValues={":username": username}
    )

    if response['Items']:
        return {'result': 'username exists'}

    user = {'email': email, 'password': password, 'username': username,} ###### add  'photo':'generic.png'
    table.put_item(Item=user)

    session["email"] = user["email"]
    session["username"] = user["username"]

    result = {'result': 'OK'}
    response = make_response(result)
    return response

@app.route('/signin.html')
def show_signin():
    return render_template("signin.html")

def is_logged_in():
    return 'email' in session

@app.route('/forget.html')
def forget():
    return render_template("forget.html")

@app.route('/get')
def get():
    email = request.args.get("email")
    if not email:
        return {'result': 'No email provided'}

    table = get_table("Users")
    item = table.get_item(Key={"email": email})
    if 'Item' not in item:
        return {'result': 'email not exists'}

    password = item['Item'].get('password')
    return {'password': password}


#profile.html

@app.route('/profile.html')
def profile():
    if not is_logged_in():
        return redirect("/")

    username = session.get("username")
    if username is None:
        return redirect("/login")

    return render_template("profile.html", username=username)

@app.route('/profile')
def listprofile():
    table = get_table('Users')
    users = table.scan()['Items']
    return {'users': users}


#logout

@app.route('/logout.html')
def logout():
    session.pop("email", None)
    session.pop("username", None)

    return redirect("/")


#user_blogs.html

@app.route('/user_blogs/<username>')
def user_blogs(username):
    if not is_logged_in():
        return redirect("/")

    users_table = get_table('Users')
    response = users_table.scan(
        FilterExpression="username = :username",
        ExpressionAttributeValues={":username": username}
    )
    if not response['Items']:
        return "User not found", 404

    user_info = response['Items'][0]
    email = user_info['email']

    # get all blogs for the current account
    blogs_table = get_table('blog')
    blogs_response = blogs_table.scan()['Items']
    user_blogs = [blog for blog in blogs_response if blog['email'] == email]

    # check if the current user is the owner
    is_owner = (session.get('email') == email)

    bucket = get_public_bucket()
    custom_photo_key = f'user_photos/{username}'
    custom_photo_exists = any(obj.key == custom_photo_key for obj in bucket.objects.all())
    if custom_photo_exists:
        photo_url = STORAGE_URL + custom_photo_key
    else:
        photo_url = STORAGE_URL + 'generic.jpg'

    return render_template("user_blogs.html", blogs=user_blogs, is_owner=is_owner, username=username, photo=photo_url)


@app.route('/delete_blog/<blog_id>', methods=['GET'])
def delete_blog(blog_id):
    table = get_table('blog')
    table.delete_item(Key={'blogID': blog_id})
    return {'result': 'Blog deleted successfully'}


@app.route('/add_blog')
def add_blog():
    blogID = str(uuid.uuid4())
    title = request.args.get("title")
    text = request.args.get("text")
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email = session['email']
    username = session.get('username')
    if not title or not text:
      return {'result':'title or text cannot be empty.'}

    blog = {
        'blogID':blogID,
        'email': email,
        'title': title,
        'text': text,
        'username': username,
        'date': date

     }
    table = get_table('blog')
    table.put_item(Item=blog)

    result = {'result':'OK'}
    response = make_response(result)
    return response


#feed.html

@app.route('/feed.html')
def feed():
    if not is_logged_in():
        return redirect("/")

    table = get_table('blog')
    results = []
    for item in table.scan(Limit=10)['Items']:
        blogID = item['blogID']
        email = item['email']
        title = item['title']
        text = item['text']
        username = item['username']
        date = item['date']

        bucket = get_public_bucket()
        custom_photo_key = f'user_photos/{username}'
        custom_photo_exists = any(obj.key == custom_photo_key for obj in bucket.objects.all())
        if custom_photo_exists:
            photo_url = STORAGE_URL + custom_photo_key
        else:
            photo_url = STORAGE_URL + 'generic.jpg'


       ####### photo = get_photo_for_user(username)######

        blog = {
            'blogID':blogID,
            'email':email,
            'title':title,
            'text':text,
            'username':username,
            'date':date,
            'photo': photo_url
        }   ###########add'photo':photo
        results.append(blog)

    results.sort(key=lambda x: x['date'], reverse=True)

    return render_template("feed.html", blogs=results)


@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    bucket = get_public_bucket()

    if 'photo' not in request.files:
        return {'error': 'No file provided'}

    photo_file = request.files['photo']
    filename = session.get('username')

    if photo_file.filename == '':
        return {'error': 'No file selected'}

    ct = 'image/jpeg'
    if filename.endswith('.png'):
        ct = "image/png"
    s3_path = 'user_photos/' + filename
    bucket.upload_fileobj(photo_file, s3_path, ExtraArgs={'ContentType':ct})

    return redirect(request.referrer)


@app.route('/<blogID>/reply')
def reply(blogID):
    if not is_logged_in():
        return redirect('/')

    blogs_table = get_table('blog')
    blog_info = blogs_table.get_item(Key={'blogID':blogID})
    if 'Item' not in blog_info:
        return "Blog not found", 404

    username = blog_info['Item'].get('username')

    bucket = get_public_bucket()
    custom_photo_key = f'user_photos/{username}'
    custom_photo_exists = any(obj.key == custom_photo_key for obj in bucket.objects.all())
    if custom_photo_exists:
        photo_url = STORAGE_URL + custom_photo_key
    else:
        photo_url = STORAGE_URL + 'generic.jpg'

    replies_table = get_table('Replies')
    replies = replies_table.scan()['Items']
    blog_replies = [reply for reply in replies if reply['blogID'] == blogID]

    return render_template("reply.html", photo=photo_url, blog=blog_info['Item'], replies=blog_replies)

@app.route('/add_reply', methods=["POST"])
def add_reply():
    replyID = str(uuid.uuid4()) + str(uuid.uuid4())
    blogID = request.form.get("blogID")
    reply_text = request.form.get("reply_text")
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email = session['email']
    username = session.get('username')

    if not reply_text:
        return {'result':'reply cannot be empty.'}

    bucket = get_public_bucket()
    custom_photo_key = f'user_photos/{username}'
    custom_photo_exists = any(obj.key == custom_photo_key for obj in bucket.objects.all())
    if custom_photo_exists:
        photo_url = STORAGE_URL + custom_photo_key
    else:
        photo_url = STORAGE_URL + 'generic.jpg'

    reply = {
        'replyID':replyID,
        'blogID':blogID,
        'reply_text':reply_text,
        'date':date,
        'email':email,
        'username':username,
        'photo':photo_url
    }

    replies_table = get_table('Replies')
    replies_table.put_item(Item=reply)

    return redirect(request.referrer)




#@app.route('/list_blogs')
#def listblogs():
#    user_email = session['email']
#    table = get_table('blog')
#
#    blogs = [
#        item for item in table.scan()['Items']
#        if item['email'] == user_email
#    ]



#   blogs_sorted = sorted(blogs, key=get_date, reverse=True)

#    response = make_response(blogs_sorted)
#    return response





#@app.route('/delete_blog/<blog_id>')
#def delete_blog(blog_id):
#    table = get_table('blog')
#    table.delete_item(
#        Key={
#            'blogID': blog_id,
#        }
#    )
#    return redirect('/blog.html')







#Instantgram
#from flask import Flask, request
#import boto3
#import json
#import uuid

#app = Flask(__name__)

# AWS Credentials and Bucket Name
#AWSKEY = 'AKIAU6GDZFPYFRYTP2YJ'
#AWSSECRET = '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'
#PUBLIC_BUCKET = 'azheng-web-public'
#STORAGE_URL = 'http://azheng-web-public.s3.amazonaws.com/'

# Get S3 Bucket
#def get_public_bucket():
#    s3 = boto3.resource(service_name='s3', region_name='us-east-2',
#                        aws_access_key_id=AWSKEY,
#                        aws_secret_access_key=AWSSECRET)
#    bucket = s3.Bucket(PUBLIC_BUCKET)
#    return bucket

# Get DynamoDB Table
#def get_images_table():
#    client = boto3.resource(service_name='dynamodb', region_name='us-east-2',
#                            aws_access_key_id=AWSKEY,
#                            aws_secret_access_key=AWSSECRET)
#    table = client.Table('Images')
#    return table

# List Files Endpoint
#@app.route('/listfiles')
#def api_listfiles():
#    table = get_images_table()
#    response = table.scan()
#
#    items = response['Items']
#    return json.dumps({'url': STORAGE_URL, 'items': items}), 200

# Upload File Endpoint
#@app.route('/uploadfile', methods=['POST'])
#def uploadfile():
#    bucket = get_public_bucket()
#    file = request.files["file"]
#    caption = request.form.get("caption", "No Caption")

    # Generate a unique imageId using filename and a random UUID
#    filename = file.filename
#    random_uuid = str(uuid.uuid4())
#    imageId = f"{filename}-{random_uuid}"

    # Upload to S3
#    ct = 'image/jpeg'
#    if filename.endswith('.png'):
#        ct = "image/png"
#    s3_path = "uploaded_images/" + imageId
#    bucket.upload_fileobj(file, s3_path, ExtraArgs={'ContentType': ct})

    # Store metadata in DynamoDB
#    table = get_images_table()
#    table.put_item(Item={
#        'imageId': imageId,  # Use generated imageId as the partition key
#        'caption': caption,
#        's3_path': STORAGE_URL + s3_path,
#    })
#
#    return json.dumps({'results': 'OK'}), 200
#
#if __name__ == '__main__':
#    app.run(debug=True)









#Apartments search
#from flask import Flask, request, jsonify, render_template

#import json
#import boto3

#app = Flask(__name__)

# load apartment data
#def load_apartments():
#    with open('/home/zzheng/mysite/apartments.json') as f:
#        return json.load(f)

#sort
#def sort_apartments(apartments, sort_order):
#    if sort_order == "Price Ascending":
#        return sorted(apartments, key=lambda x: x['monthly_rent'])
#    elif sort_order == "Price Descending":
#        return sorted(apartments, key=lambda x: x['monthly_rent'], reverse=True)
#    return apartments

#@app.route('/')
#def index():
#    return render_template('index.html')

#@app.route('/search', methods=['GET'])
#def search():
#    query = request.args.get('query', '').lower()
#    bedrooms = request.args.get('bedrooms', 'Any')
#    sort_order = request.args.get('sort', 'None')

#    apartments = load_apartments()

#    # filter
#   filtered_apartments = [
#        apt for apt in apartments
#        if (query in apt['title'].lower() or query in apt['description'].lower()) and
#           (bedrooms == 'Any' or apt['numberofbedroom'] >= int(bedrooms[:-1]))
#    ]

    # sort
#    sorted_apartments = sort_apartments(filtered_apartments, sort_order)

#    return jsonify(sorted_apartments)

#if __name__ == '__main__':
#   app.run(debug=True)