from flask import render_template, url_for,flash,redirect,request
from app import app, db,bcrypt
from app.models import User,Post
from app.forms import RegistrationForm,LoginForm, UpdateAccountForm,PostForm
from flask_login import login_user, current_user,logout_user,login_required
import secrets
import os
from PIL import Image





@app.route('/')
def home():
    posts = Post.query.all()
    return render_template('home.html',posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register',methods=['POST','GET'])
def register():
    if current_user.is_authenticated: #checks if current user is authenticated so it doesn't move to the register page again
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
 
        flash(f'Account created successfully! You can login now', 'success')
        return redirect (url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated: #checks if current user is authenticated so it doesn't move to the login page again
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next') #query parameter gotten when we try to access account page
            return redirect(next_page) if next_page else redirect(url_for('home'))

        else:
            flash('Login unsuccessful. check your credentials','danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    #_ the underscores in python means a variable not used in my application
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path,'static/images',picture_fn)
    output_size =(125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route('/account',methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data 
        current_user.email = form.email.data 
        db.session.commit()
        flash('Your account has been updated!','success')
        return redirect(url_for('account')) #this helps prevent that pop ups on your browser about re-submitting forms
    elif request.method =='GET':
        # these below two codes helps populate our form data with user details automatically in account page
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static',filename='images/'+ current_user.image_file)
    return render_template('account.html',image_file=image_file,form=form)


# create post
@app.route('/post/new',methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post) #adds contents to database
        db.session.commit() #commits session to the database
        flash('Your post has been created!','success')
        return redirect(url_for('home'))
    return render_template('create_post.html',title="Create Post",form=form)


@app.route('/post/<int:post_id>',methods=['GET','POST'])
@login_required
def post_details(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_details.html',title=post.title,post=post)



with app.app_context():
    db.create_all()