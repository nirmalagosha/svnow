from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
app=Flask('__name__')
#config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'
#init MySQL
mysql=MySQL(app)
@app.route('/')
def home():
    return render_template('home.html');
@app.route('/about')
def about():
    return render_template('about.html')
# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=1,max=25)])
    email=StringField('Email',[validators.Email(message='Enter valid Email')])
    password=PasswordField('Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm',message='Passwords Do not Match ')
    ])
    confirm=PasswordField('confirm password')
#Register
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data;
        email=form.email.data;
        username=form.password.data
        password=sha256_crypt.encrypt(str(form.password.data))
        #create cursor
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO users (name,username,email,password) values(%s,%s,%s,%s)",(name,username,email,password))
        #commit
        mysql.connection.commit()
        #close the curosr
        cur.close()
        flash('Your are Registered and good to go','success')
        return redirect(url_for('register'))
        #return render_template('register.html',form=form)
    return render_template('register.html',form=form)
#userLogin
@app.route('/login',methods=['GET','POST'])
def login():
    #GET form fields
    if request.method=='POST':
        username=request.form['username']
        password_candidate=request.form['password']
        #create DictCursor
        cur=mysql.connection.cursor()
        #get suer by username
        result=cur.execute("select * from users where username=%s",[username])
        if result>0:
            #get stored hash
            data=cur.fetchone()
            password=data['password']
            #compare password_candidate
            if sha256_crypt.verify(password_candidate,password):
                #Passed
                session['logged_in']=True
                session['username']=username
                flash('You are logged in','success')
                return render_template('dashboard.html')
            else:
                error='Password not matched'
                #app.logger.info('Password did not match')
                return render_template('login.html',error=error)
        else:
            error='Username not found'
            return render_template('login.html',error=error)
    return render_template('login.html')
#Check if user is logged_in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthourized ,Please login','danger')
            return redirect(url_for('login'))
    return wrap

#Dashboard
@app.route('/dashboard')
@is_logged_in #checks if user is logged in or not
def dashboard():
    #Fetch all Articles
    cur=mysql.connection.cursor()
    #get them
    result=cur.execute("select * from articles")
    articles=cur.fetchall()

    if result>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg="No Articles Found"
        return render_template('dashboard.html',msg=msg)
    cur.close()
#Logout
@app.route('/Logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are logged out','success')
    return redirect(url_for('login'))
#Article Form class
class ArticleForm(Form):
    title=StringField('Title',[validators.Length(min=1,max=50)])
    body=TextAreaField('Body',[validators.Length(min=30)])
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in #checks if user is logged in or not
def add_article():
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate():
        title=form.title.data
        body=form.body.data
        #Create curosr
        cur=mysql.connection.cursor()
        #execute
        cur.execute("INSERT INTO articles(title,body,author)values(%s,%s,%s)",[title,body,session['username']])
        #commit
        mysql.connection.commit()
        #close
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
#Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['TITLE']
    form.body.data = article['BODY']

    if request.method == 'POST' and form.validate():
        title = request.form['TITLE']
        body = request.form['BODY']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)
# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))



if __name__=='__main__':
    app.secret_key='secret12345'
    app.run(debug=True)
