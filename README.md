# renpy-shader

Experimental OpenGL shader and skeletal animation support for Ren'Py. The ShaderDemo Ren'Py project included in this repository has many examples about what this library can do.

# Requirements

* Graphics card with a decent OpenGL support.
* Ren'Py version 6.99.x (might work with older ones, but it's not supported).
* Windows or OS X. Should work in Linux, too, but it's currently untested.

# Installation

1. Clone or download this repository to your machine.

2. Copy the contents of the "pythonlib2.7"-directory to your Ren'Py SDK installation subdirectory "lib/pythonlib2.7". This is required because Ren'Py ships with a stripped down Python standard library which is missing some required files.

3. Download [PyOpenGL](https://pypi.python.org/pypi/PyOpenGL/3.1.1a1) and place it's uncompressed package subdirectory "OpenGL" (the one which contains the \__init__.py) either under this project's "ShaderDemo/game"-directory or under the Ren'Py SDK's "lib/pythonlib2.7".

4. Start the ShaderDemo and run the demos or the rig editor.

# Links

* [Shader effects demo video](https://www.youtube.com/watch?v=nyDbvAy0Xa4)
* [Skeletal animation demo video](https://www.youtube.com/watch?v=LL2GuJG_2E0)
