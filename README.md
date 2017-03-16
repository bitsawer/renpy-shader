# renpy-shader

OpenGL shader and [skeletal animation](doc/rigeditor.md) support for Ren'Py. The ShaderDemo Ren'Py project included in this repository has many examples about what this library can do.

# Examples

* [Shader effects demo video](https://www.youtube.com/watch?v=nyDbvAy0Xa4)
* [Skeletal rig animation demo video](https://www.youtube.com/watch?v=LL2GuJG_2E0)
* [Rig editor basics](https://www.youtube.com/watch?v=NHJu0OYBERE)

# Requirements

* Graphics card with a decent OpenGL support.
* Ren'Py version 6.99.x (might work with older ones, but it's not supported).
* Supports Windows, OS X and Linux (tested on Ubuntu). No Android or iOS support (at least not yet).

# Installation

1. Clone or download this repository to your machine.

2. Copy the contents of the "pythonlib2.7"-directory to your Ren'Py SDK installation subdirectory "lib/pythonlib2.7". This is required because Ren'Py ships with a stripped down Python standard library which is missing some required files.

3. Clone or download [PyOpenGL](https://github.com/mcfletch/pyopengl) and place it's uncompressed package subdirectory "OpenGL" (the one which contains the \__init__.py) either under this project's "ShaderDemo/game"-directory or under the Ren'Py SDK's "lib/pythonlib2.7".

4. Start the ShaderDemo and run the demos or the rig editor.
