
import ctypes
from OpenGL import GL as gl

class ShaderProgram:
    def __init__(self, vsCode, psCode):
        self.handle = gl.glCreateProgram()
        self.linked = False

        self.createShader(vsCode, gl.GL_VERTEX_SHADER)
        self.createShader(psCode, gl.GL_FRAGMENT_SHADER)

        self.link()

        if not self.linked:
            raise RuntimeError("Shader not linked")

    def createShader(self, shaderCode, type):
        shader = gl.glCreateShader(type)
        gl.glShaderSource(shader, shaderCode)
        gl.glCompileShader(shader)

        status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if status:
            gl.glAttachShader(self.handle, shader)
        else:
            raise RuntimeError("Shader compile error: %s" % gl.glGetShaderInfoLog(shader))

    def link(self):
        gl.glLinkProgram(self.handle)

        status = gl.glGetProgramiv(self.handle, gl.GL_LINK_STATUS)
        if status:
            self.linked = True
        else:
            raise RuntimeError("Link error: %s" % gl.glGetProgramInfoLog(self.handle))

    def free(self):
        if self.handle:
            gl.glDeleteProgram(self.handle)
            self.handle = 0
        self.linked = False

    def bind(self):
        gl.glUseProgram(self.handle)

    def unbind(self):
        gl.glUseProgram(0)

    def uniformf(self, name, *values):
        {1 : gl.glUniform1f,
         2 : gl.glUniform2f,
         3 : gl.glUniform3f,
         4 : gl.glUniform4f
        }[len(values)](gl.glGetUniformLocation(self.handle, name), *values)

    def uniformi(self, name, *values):
        {1 : gl.glUniform1i,
         2 : gl.glUniform2i,
         3 : gl.glUniform3i,
         4 : gl.glUniform4i
        }[len(values)](gl.glGetUniformLocation(self.handle, name), *values)

    def uniformMatrix4f(self, name, matrix):
        loc = gl.glGetUniformLocation(self.handle, name)
        gl.glUniformMatrix4fv(loc, 1, False, (ctypes.c_float * 16)(*matrix))

    def uniformMatrix4fArray(self, name, values):
        loc = gl.glGetUniformLocation(self.handle, name)
        count = len(values) / 16
        gl.glUniformMatrix4fv(loc, count, False, (ctypes.c_float * len(values))(*values))
