from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, login_required, RoleMixin, Security, SQLAlchemyUserDatastore, UserMixin, utils
from flask_admin import Admin, AdminIndexView
from flask_sslify import SSLify

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_ECHO'] = True
sslify = SSLify(app)
db = SQLAlchemy(app)

app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
# Replace this with your own salt.
app.config['SECURITY_PASSWORD_SALT'] = '2kxfa[0ufqpnjnakdsnf928ef*f92j9pjf8*J*JFSDFjKij8u8u*(&$*((#*&$(&)#@*&$*#&*@(&$()@&#$)*@#%&%*@#aF~`<...........&623492jafsd11034f'


roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str_(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
            'Role', secondary=roles_users,
            backref=db.backref('users', lazy='dynamic')
            )

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def before_first_request():

    db.create_all()

    user_datastore.find_or_create_role(name='admin', description='Adminstrator')
    # choose your own password between quotes below
    encrypted_password = utils.encrypt_password('')
    # enter your email between the quotes
    if not user_datastore.get_user(''):
        # enter email between quotes below
        user_datastore.create_user(email='', password=encrypted_password)

    db.session.commit()
    # enter email between quotes below
    user_datastore.add_role_to_user('', 'admin')
    db.session.commit()

@app.route('/login')
@login_required
def login():
    return redirect('/admin')

class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    author = db.Column(db.String(20))
    date_posted = db.Column(db.DateTime)
    content = db.Column(db.Text)

    def __unicode_(self):
        return self.name

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(ModelView(Blogpost, db.session))


@app.route('/')
def index():
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).limit(3).all()

    return render_template('index.html', posts=posts)

@app.route('/olderposts')
def olderposts():
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).all()

    return render_template('olderposts.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Blogpost.query.filter_by(id=post_id).one()

    return render_template('post.html', post=post)


@app.route('/addpost', methods=['POST'])
def addpost():
    title = request.form['title']
    subtitle = request.form['subtitle']
    author = request.form['author']
    content = request.form['content']

    post = Blogpost(title=title, subtitle=subtitle, author=author, content=content, date_posted=datetime.now())

    db.session.add(post)
    db.session.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':

    # Build sample db on the fly, if one does not exist yet.
    db.create_all()
    app.run(debug=True)
