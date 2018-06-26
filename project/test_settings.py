
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/backend.db.sqlite3',
    },
    'products': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'product',
        'USER': 'guestuser',
        'PASSWORD': 'v&BBKPhXrTZ3',
        'HOST': 'rm-2ze939rx0u3ws858o.mysql.rds.aliyuncs.com',
        'PORT': '3306',
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
            'MIRROR': 'products',
        }
    },
}

# every single db requires one DB router
# DefaultRouter always the last one
DATABASE_ROUTERS = ('project.database_router.ProductRouter',
                    'project.database_router.DefaultRouter')
