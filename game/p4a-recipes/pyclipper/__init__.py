from pythonforandroid.recipe import CMakeRecipe
from os.path import join

class PyClipperRecipe(CMakeRecipe):
    version = "1.3.0.post6"
    url = "https://github.com/mrbliss/pyclipper/archive/refs/tags/v{version}.tar.gz"
    name = "pyclipper"
    depends = []
    built_libraries = [join("build", "libclipper.so")]

    def get_recipe_env(self):
        env = super().get_recipe_env()
        env["CXXFLAGS"] = "-std=c++11"
        return env

    def prebuild(self):
        # Install additional build dependencies if required
        pass
