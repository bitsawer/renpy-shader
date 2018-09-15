# renpy-shader

OpenGL shader and [skeletal animation](doc/rigeditor.md) support for Ren'Py. The ShaderDemo Ren'Py project included in this repository has many examples about what this library can do.

# Examples

* [Shader effects demo video](https://www.youtube.com/watch?v=nyDbvAy0Xa4)
* [Deferred shading demo video](https://www.youtube.com/watch?v=FceQEEXn7Bg)
* [Skeletal rig animation demo video](https://www.youtube.com/watch?v=LL2GuJG_2E0)
* [Rig editor basics](https://www.youtube.com/watch?v=NHJu0OYBERE)

# Requirements

* Graphics card with a decent OpenGL support.
* Ren'Py version 6.99.x (might work with older ones, but it's not supported).
* Supports Windows, OS X and Linux (tested on Ubuntu). No Android or iOS support (at least not yet).

# Installation

If you are updating your local version instead of installing the first time, it is recommended that you first remove all files belonging to this library before copying in the new ones. Otherwise if files are renamed, moved etc. old files might be lying around and cause some hard-to-debug naming or behavior conflicts with new files.

1. Clone or download this repository to your machine.

2. **This step is not always needed if you are using Ren'Py 7.x or newer.** Copy the contents of the "pythonlib2.7"-directory to your Ren'Py SDK installation subdirectory "lib/pythonlib2.7". This is required because some versions of Ren'Py ship with a stripped down Python standard library which is missing some required files.

3. Download [PyOpenGL](https://pypi.python.org/pypi/PyOpenGL/3.1.1a1) and place its uncompressed package subdirectory "OpenGL" (the one which contains the \__init__.py) either under this projects "ShaderDemo/game"-directory or under the Ren'Py SDK's "lib/pythonlib2.7". If you are using Linux you might want to get the latest version directly from the [repository](https://github.com/mcfletch/pyopengl), but don't do this on Windows or Mac unless PyOpenGL does not get imported correctly. 

4. Start the ShaderDemo and run the demos or the rig editor.

# Troubleshooting

**1) An exception occurs when starting the game: "TypeError: 'NoneType' object is not callable"**

You probably forgot to do installation step 2 or you put the files in a wrong place.

**2) An exception occurs when starting the game: "ImportError: No module named OpenGL"**

You probably forgot to do installation step 3 or you put the files in a wrong place. 

**3) An exception occurs when starting the game: "AttributeError: 'NoneType' object has no attribute 'glGetError'"**

Some versions of PyOpenGL can have issues with certain platforms. Try the latest (or alternatively the older official) PyOpenGL source code.

**4) Shader effects are not applied and/or rigs are not moving.**

You are probably seeing the normal, static fallback images. Make sure the computer and RenPy mode (OpenGL vs software) supports shaders. Most should if the computer is not ancient and the graphics card is not blacklisted. Also make sure that the effects have not been disabled by setting "shader.config.enabled" to False or by the user in the preferences screen (persistent.shader_effects_enabled).
