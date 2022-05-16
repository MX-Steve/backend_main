from os import path
from distutils.core import Command
from setuptools import setup


class GenerateGRPCStub(Command):
    """ Generate GRPC stubs """

    user_options = [
        ('output-dir=', 'o', 'output directory'),
    ]

    def initialize_options(self):
        self.output_dir = None

    def finalize_options(self):
        if self.output_dir is None or not path.isdir(self.output_dir):
            raise Exception(f"Invalid output directory: {self.output_dir}")

    def run(self, *args, **_):
        # pylint: disable=import-outside-toplevel
        from grpc_tools import protoc
        # pylint: enable=import-outside-toplevel
        idl_dir = path.abspath(
            path.join(path.dirname(path.realpath(__file__)), 'idl'))
        output_dir = self.output_dir
        args = (['', '-I', path.join(idl_dir, 'schemas/server'),
                     f'--python_out={output_dir}',
                     f'--grpc_python_out={output_dir}',
                     path.join(idl_dir, 'schemas/server/djentry.proto')])
        protoc.main(args)
        GenerateGRPCStub.patch_grpc_import_path(
            path.join(output_dir, 'djentry_pb2_grpc.py'))

    @staticmethod
    def patch_grpc_import_path(fn):
        data = None
        with open(fn, 'rb') as f:
            data = f.read().decode('utf-8')
        patched = data.replace(
            'import djentry_pb2 as djentry__pb2', 'from . import djentry_pb2 as djentry__pb2')
        with open(fn, 'wb') as f:
            f.write(patched.encode('utf-8'))


install_requirements = ['setuptools', 'Django==3.2.7',
                        'grpcio==1.41.0', 'grpcio-tools==1.41.0', 'PyMySQL==1.0.2']

dev_requirements = ['pylint', 'mock', 'pylint-django']

setup(name='djentry',
      install_requires=install_requirements,
      extras_require={'dev': dev_requirements},
      cmdclass={'gen_grpc': GenerateGRPCStub},
      )
