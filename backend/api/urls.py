from django.urls import include, path

urlpatterns = [
    path('users/', include('users.urls')),
    path('recipes/', include('recipes.urls', namespace='recipes')),
    path('auth/', include([
        path('', include('djoser.urls')),
        path('', include('djoser.urls.authtoken')),
    ])),
]