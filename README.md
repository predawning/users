This a demo about user login/register rest APIs


# How to set up the users system on OS X

## Preparation

1. Install [Homebrew](http://brew.sh/index.html "Homebrew/brew")

	Homebrew is a free and open-source software package management system
	that simplifies the installation of software on OS X.
	
		ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
		
		
2. Install Python 3.5
				
			
3. Install gettext

	This is required by translation.
	
		brew install gettext
		brew link gettext --force
		
		
4. Install MySQL

		brew install mysql 
		brew services start mysql
		
5. Install Redis

		brew install redis
		brew services start redis

		
## Installation
		
1. Create MySQL database

		# the database owned by postgres
		mysql> create database product
		mysql> create database station
		
3. Download source of the users system

		# configure git if not configured
		git config --global user.name "<your full name>"
		git config --global user.email <your email>
		git config --global core.editor vim
		
		git clone https://github.com/predawning/users.git
		
		
4. Configure the users system
	
	* Create local_settings.py( DON'T NEED if configuring DEVELOPMENT environment. )

			cd users/project
			cp local_settings.py.example local_settings.py
			
	* Update database configuration
	
		Comment out all statements in local_settings.py and then add the following to it.
		This is based on the 'DATABASES' in settings.py in the same directory.
	
		```
        DATABASES['default']['HOST'] = 'localhost'
        DATABASES['default']['PORT'] = '3306'
        DATABASES['default']['NAME'] = 'station'
        DATABASES['default']['USER'] = 'root'
        DATABASES['default']['PASSWORD'] = ''
        
	    ```
	* Install system packages, this works for Ubuntu, For mac system, please use brew to install accordingly
	
		bash requrirements.system
		
			

5. Set up Python 3.5 virtual environment
	
	A virtual environment has its own site directories, optionally isolated from system site directories.
	It also has its own Python binary and can have its own independent set of installed Python packages in its site directories.
	
        cd users
        # activate the virtual environment
        pipenv shell
        # install necessary dependencies, especially Django
        pip install -r requirements.txt
        # exit
    		

        
6. Run the users system
    		
	* Activate the virtual environment
	
	```
	    cd users
	    pipenv shell
	```
			
	* Initialize or update the database
    
    ```
        ./manage.py migrate
        ./manage.py migrate --database
    ```
			
	* Test the users system

    ```
        ./manage.py test
    ```
    		
	* Prepare localization and staticfiles
    
    ```
        ./manage.py compilemessages
        ./manage.py collectstatic
	```
			
	* Create a super user
	
        This is used to log in on the Django Admin Site.
	
    ```
        ./manage.py createsuperuser
    ```
        
	* Start the users system
	
    ```
        ./manage.py runserver
    ```
    			
	The users system is now available on 
    
    ```
        http://localhost:8000/admin
    ```
     
    This is the Django Admin Site.
	It is used to manage models of Django applications registered on Django.
	
	The API document and testing page:
    ```
        http://localhost:8000/docs
    ```


# Translation

To generate/update the messages files:

	./manage.py makemessages -l zh_Hans
	
To compile the translated messages files:

	./manage.py compilemessages
	

# RESTful API

As Django rest framework requirement, Use `GET` to fetch, `POST` to create and `PUT` to change object.

However sometimes, we also use the `POST` method to change object as well. It is our custom rule:

    PUT will be used when <object_id> in url, otherwise replace the API with POST method
    
The API interface is :
    
    http://localhost:8000/api/v1/

