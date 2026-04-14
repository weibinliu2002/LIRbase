from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/<str:division>/", views.species_list, name="species_list"),
    path("species/<str:accession>/", views.species_detail, name="species_detail"),
    path("lir/<str:accession>/<path:lir_id>/", views.lir_detail, name="lir_detail"),

    path("search/region/", views.search_by_region, name="search_by_region"),
    path("search/id/", views.search_by_id, name="search_by_id"),
    path("search/blast/", views.search_blast, name="search_blast"),
    path("annotate/", views.annotate_page, name="annotate_page"),
]