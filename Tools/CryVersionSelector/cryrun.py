#!/usr/bin/env python3

import sys
import argparse
import os.path
import subprocess
import shutil

import configparser
import tempfile
import datetime
import zipfile
import stat

from win32com.shell import shell, shellcon

import cryproject, cryregistry

#--- errors

def error_project_not_found (path):
	sys.stderr.write ("'%s' not found.\n" % path)
	sys.exit (404)

def error_project_json_decode (path):
	sys.stderr.write ("Unable to parse '%s'.\n" % path)
	sys.exit (1)

def error_cmake_not_found():
	sys.stderr.write ("Unable to locate CMake.\n")
	sys.exit (1)

def error_engine_tool_not_found (path):
	sys.stderr.write ("'%s' not found.\n" % path)
	sys.exit (404)
	
def error_mono_not_set (path):
	sys.stderr.write ("'%s' is not a C# project.\n" % path)
	sys.exit (1)

def error_mono_not_found (path):
	sys.stderr.write ("'%s' not found.\n" % path)
	sys.exit (1)

def error_upgrade_engine_version (engine_version):
	sys.stderr.write ("Unknown engine version: %s.\n" % path)
	sys.exit (1)

def error_upgrade_template_unknown (project_file):
	sys.stderr.write ("Unable to identify original project template for '%s'.\n" % path)
	sys.exit (1)

def error_upgrade_template_missing (restore_path):
	sys.stderr.write ("Missing upgrade information '%s'.\n" % restore_path)
	sys.exit (1)
		
def print_subprocess (cmd):
	print (' '.join (map (lambda a: '"%s"' % a, cmd)))

#---

def get_cmake_path():
	program= 'cmake.exe'
	path= shutil.which (program)
	if path:
		return path
		
	path= os.path.join (shell.SHGetFolderPath (0, shellcon.CSIDL_PROGRAM_FILES, None, 0), 'CMake', 'bin', program)
	if os.path.isfile (path):
		return path
	
	path= os.path.join (shell.SHGetFolderPath (0, shellcon.CSIDL_PROGRAM_FILESX86, None, 0), 'CMake', 'bin', program)
	if os.path.isfile (path):
		return path
	
	return None

def get_engine_path():
	if getattr( sys, 'frozen', False ):
		ScriptPath= sys.executable
	else:
		ScriptPath= __file__
		
	return os.path.abspath (os.path.join (os.path.dirname(ScriptPath), '..', '..'))
		

def get_solution_dir (args):
	basename= os.path.basename (args.project_file)
	return os.path.join ('Solutions', "%s.%s" % (os.path.splitext (basename)[0], args.platform))
	#return os.path.join ('Solutions', os.path.splitext (basename)[0], args.platform)
	

#--- PROJGEN ---

def cmd_projgen(args):
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)
	
	project= cryproject.load (args.project_file)
	if project is None:
		error_project_json_decode (args.project_file)
	
	cmake_path= get_cmake_path()
	if cmake_path is None:
		error_cmake_not_found()
		
	#---
		
	project_path= os.path.dirname (args.project_file)
	solution_path= os.path.join (project_path, get_solution_dir (args))
	engine_path= get_engine_path()
	
	subcmd= (
		cmake_path,
		'-Wno-dev',
		{'win_x86': '-AWin32', 'win_x64': '-Ax64'}[args.platform],
		'-DPROJECT_FILE:FILEPATH=%s' % os.path.abspath (args.project_file),
		'-DCryEngine_DIR:PATH=%s' % engine_path,
		'-DCMAKE_PREFIX_PATH:PATH=%s' % os.path.join (engine_path, 'Tools', 'CMake', 'modules'),
		'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG:PATH=%s' % os.path.join (project_path, cryproject.shared_dir (project, args.platform, 'Debug')),
		'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE:PATH=%s' % os.path.join (project_path, cryproject.shared_dir (project, args.platform, 'Release')),
		'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_MINSIZEREL:PATH=%s' % os.path.join (project_path, cryproject.shared_dir (project, args.platform, 'MinSizeRel')),		
		'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELWITHDEBINFO:PATH=%s' % os.path.join (project_path, cryproject.shared_dir (project, args.platform, 'RelWithDebInfo')),
		os.path.join (project_path, cryproject.cmakelists_dir(project))
	)
	
	if not os.path.isdir (solution_path):
		os.makedirs (solution_path)

	os.chdir (solution_path)
	print_subprocess (subcmd)
	sys.exit (subprocess.call(subcmd))
	
#-- BUILD ---

def cmd_build(args):
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)
	
	cmake_path= get_cmake_path()
	if cmake_path is None:
		error_cmake_not_found()
	
	#---

	project_path= os.path.dirname (os.path.abspath (args.project_file))
	solution_dir= get_solution_dir (args)
	
	subcmd= (
		cmake_path,
		'--build', solution_dir,
		'--config', args.config
	)
	
	os.chdir (project_path)
	print_subprocess (subcmd)
	sys.exit (subprocess.call(subcmd))

#--- OPEN ---

def cmd_open (args):
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)
	
	tool_path= os.path.join (get_engine_path(), 'bin', args.platform, 'GameSDK.exe')
	if not os.path.isfile (tool_path):
		error_engine_tool_not_found (tool_path)
		
	#---
	
	subcmd= (
		tool_path,
		'-project',
		os.path.abspath (args.project_file)
	)
	
	print_subprocess (subcmd)
	subprocess.Popen(subcmd)

#--- EDIT ---

def cmd_edit(argv):
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)
	
	tool_path= os.path.join (get_engine_path(), 'bin', args.platform, 'Sandbox.exe')
	if not os.path.isfile (tool_path):
		error_engine_tool_not_found (tool_path)
		
	#---

	subcmd= (
		tool_path,
		'-project',
		os.path.abspath (args.project_file)
	)

	print_subprocess (subcmd)
	subprocess.Popen(subcmd)

#--- MONO ---

def cmd_monodev (args):	
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)	

	project= cryproject.load (args.project_file)
	if project is None:
		error_project_json_decode (args.project_file)
			
	mono_solution= project.get ('monodev', {}).get ('solution')
	if mono_solution is None:
		error_mono_not_set (args.project_file)
	
	mono_solution= os.path.abspath (os.path.join (os.path.dirname (args.project_file), mono_solution))
	if not os.path.isfile (mono_solution):
		error_mono_not_found (mono_solution)
	
	engine_path= get_engine_path()
	tool_path= os.path.join (engine_path, 'Tools', 'MonoDevelop', 'bin', 'MonoDevelop.exe')
	if not os.path.isfile (tool_path):
		error_engine_tool_not_found (tool_path)

	#---

	subcmd= (
		tool_path,
		mono_solution
	)

	print_subprocess (subcmd)
	subprocess.Popen(subcmd, env= dict(os.environ, CRYENGINEROOT=engine_path))
					 
def upgrade_identify (project_file):
	code_path= os.path.join (os.path.dirname (project_file), 'Code')
	
	listdir= os.listdir (code_path)	
	if all ((filename in listdir) for filename in ('Game', 'SampleApp', 'SampleApp.sln')):
		return ('cs', 'Blank')

	if all ((filename in listdir) for filename in ('Game', 'EditorApp', 'SandboxInteraction.sln')):
		return ('cs', 'SandboxInteraction')

	if all ((filename in listdir) for filename in ('Game', 'Sydewinder', 'Sydewinder.sln')):
		return ('cs', 'Sydewinder')
	
	if all ((filename in listdir) for filename in ('Game', )):
		return ('cpp', 'Blank')

	return None	
	
	
def cmd_upgrade (args):
	if not os.path.isfile (args.project_file):
		error_project_not_found (args.project_file)

	try:		
		file= open (args.project_file, 'r')
		project= configparser.ConfigParser()
		project.read_string ('[project]\n' + file.read())
		file.close()
	except ValueError:
		error_project_json_decode (args.project_file)
		
	engine_version= project['project'].get ('engine_version')
	restore_version= {
	'5.0.0': '5.0.0',
	'5.1.0': '5.1.0',
	'5.1.1': '5.1.0'
	}.get (engine_version)
	if restore_version is None:
		error_upgrade_engine_version (engine_version)
	
	template_name= upgrade_identify (args.project_file)
	if template_name is None:
		error_upgrade_template_unknown (arg.project_file)
	
	restore_path= os.path.abspath (os.path.join ('upgrade', restore_version, *template_name) + '.zip')
	if not os.path.isfile (restore_path):
		error_upgrade_template_missing (restore_path)
		
	#---
	
	(dirname, basename)= os.path.split (os.path.abspath (args.project_file))
	cwd= os.getcwd()
	os.chdir (dirname)
		
	(fd, zfilename)= tempfile.mkstemp('.zip', datetime.date.today().strftime ('upgrade_%y%m%d_'), dirname)
	file= os.fdopen(fd, 'wb')
	backup= zipfile.ZipFile (file, 'w', zipfile.ZIP_DEFLATED)
	restore= zipfile.ZipFile (restore_path, 'r')

	#.bat
	for filename in (basename, 'Code_CPP.bat', 'Code_CS.bat', 'Editor.bat', 'Game.bat', 'CMakeLists.txt'):
		if os.path.isfile (filename):
			backup.write (filename)

	#bin	
	for (dirpath, dirnames, filenames) in os.walk ('bin'):
		for filename in filter (lambda a: os.path.splitext(a)[1] in ('.exe', '.dll'), filenames):
			backup.write (os.path.join (dirpath, filename))
	
	#Solutions
	for (dirpath, dirnames, filenames) in os.walk ('Code'):
		for filename in filter (lambda a: os.path.splitext(a)[1] in ('.sln', '.vcxproj', '.filters', '.user', '.csproj'), filenames):
			path= os.path.join (dirpath, filename)
			backup.write (path)

	backup_list= backup.namelist()

	#Files to be restored
	for filename in restore.namelist():
		if os.path.isfile (filename) and filename not in backup_list:
			backup.write (filename)

	#---
	
	backup.close()
	file.close()
	
	#Delete files backed up
	
	z= zipfile.ZipFile (zfilename, 'r')
	for filename in z.namelist():
		os.chmod(filename, stat.S_IWRITE)
		os.remove (filename)
	z.close()
	
	restore.extractall()
	restore.close()

#--- REQUIRE ---

def require_getall (registry, require_list, result):
	
	for k in require_list:
		if k in result:
			continue

		project_file= cryregistry.project_file (registry, k)
		project= cryproject.load (project_file)
		result[k]= cryproject.require_list (project)
	
def require_sortedlist (d):
	d= dict (d)
	
	result= []
	while d:
		empty= [k for (k, v) in d.items() if len (v) == 0]
		for k in empty:
			del d[k]
		
		for key in d.keys():
			d[key]= list (filter (lambda k: k not in empty, d[key]))
						
		empty.sort()
		result.extend (empty)

	return result

def cmd_require (args):	
	registry= cryregistry.load()
	project= cryproject.load (args.project_file)
	
	plugin_dependencies= {}
	require_getall (registry, cryproject.require_list(project), plugin_dependencies)
	plugin_list= require_sortedlist (plugin_dependencies)
	plugin_list= cryregistry.filter_plugin (registry, plugin_list)
	
	project_path= os.path.dirname (args.project_file)
	plugin_path= os.path.join (project_path, 'cryext.txt')
	if os.path.isfile (plugin_path):
		os.remove (plugin_path)
		
	plugin_file= open (plugin_path, 'w')
	for k in plugin_list:
		project_file= cryregistry.project_file (registry, k)
		project_path= os.path.dirname (project_file)
		project= cryproject.load (project_file)
		
		(m_extensionName, shared_path)= cryproject.shared_tuple (project, args.platform, args.config)
		asset_dir= cryproject.asset_dir (project)
		
		m_extensionBinaryPath= os.path.normpath (os.path.join (project_path, shared_path))
		m_extensionAssetDirectory= asset_dir and os.path.normpath (os.path.join (project_path, asset_dir)) or ''
		m_extensionClassName= 'EngineExtension_%s' % os.path.splitext (os.path.basename (m_extensionBinaryPath))[0]

		line= ';'.join ((m_extensionName, m_extensionClassName, m_extensionBinaryPath, m_extensionAssetDirectory))
		plugin_file.write  (line + os.linesep)
		
	plugin_file.close()

#--- MAIN ---


if __name__ == '__main__':
	parser= argparse.ArgumentParser()
	parser.add_argument ('--platform', default= 'win_x64', choices= ('win_x86', 'win_x64'))
	parser.add_argument ('--config', default= 'RelWithDebInfo', choices= ('Debug', 'Release', 'RelWithDebInfo', 'MinSizeRel'))
	
	subparsers= parser.add_subparsers(dest='command')
	subparsers.required= True
		
	parser_upgrade= subparsers.add_parser ('upgrade')
	parser_upgrade.add_argument ('project_file')
	parser_upgrade.add_argument ('--engine_version')
	parser_upgrade.set_defaults(func=cmd_upgrade)
	
	parser_require= subparsers.add_parser ('require')
	parser_require.add_argument ('project_file')
	parser_require.set_defaults(func=cmd_require)
	
	parser_projgen= subparsers.add_parser ('projgen')
	parser_projgen.add_argument ('project_file')
	parser_projgen.set_defaults(func=cmd_projgen)
	
	parser_build= subparsers.add_parser ('build')
	parser_build.add_argument ('project_file')
	parser_build.set_defaults(func=cmd_build)
	
	parser_open= subparsers.add_parser ('open')
	parser_open.add_argument ('project_file')
	parser_open.set_defaults(func=cmd_open)
	
	parser_edit= subparsers.add_parser ('edit')
	parser_edit.add_argument ('project_file')
	parser_edit.set_defaults(func=cmd_edit)
	
	parser_mono= subparsers.add_parser ('monodev')
	parser_mono.add_argument ('project_file')
	parser_mono.set_defaults(func=cmd_monodev)

	args= parser.parse_args()
	args.func (args)