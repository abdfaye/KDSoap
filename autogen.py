import os, sys, subprocess

from cpack import CPackGenerateConfiguration 
from configure import ConfigureScriptGenerator
from header import ForwardHeaderGenerator

def checkVCS( sourceDirectory ):
	p = subprocess.Popen( ["git", "rev-parse", "HEAD"], cwd = sourceDirectory, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	( stdout, stderr ) = p.communicate()
	if p.returncode == 0:
		revision = stdout.strip()[:8]
		return ( revision, False ) #TODO check if tagged

	# check repository URL
	p = subprocess.Popen( ["svn", "info"], cwd = sourceDirectory, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
	( stdout, stderr ) = p.communicate()
	if p.returncode != 0:
		p = subprocess.Popen( ["git", "svn", "info"], cwd = sourceDirectory, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
		( stdout, stderr ) = p.communicate()
	if p.returncode != 0:
		print_stderr( "Error: Not an SVN nor Git repository: {0}".format( sourceDirectory ) )
		sys.exit( 1 )

	repositoryUrl = stdout.splitlines()[1].split( ':', 1 )[1]
	repositoryRevision = stdout.splitlines()[4].split( ':', 1 )[1].strip()
	isTagged = repositoryUrl.find('/tags/') != -1
	return ( repositoryRevision, isTagged )

def autogen(project, version, subprojects, prefixed, forwardHeaderMap = {}, steps=["generate-cpack", "generate-configure", "generate-forward-headers"], installPrefix="$$INSTALL_PREFIX", policyVersion = 1):
	global __policyVersion
	__policyVersion = policyVersion
	sourceDirectory = os.path.abspath( os.path.dirname( os.path.dirname( __file__ ) ) )
	buildDirectory = os.getcwd()

	print( "-- Using source directory: {0}".format( sourceDirectory ) )

	( repositoryRevision, isTagged ) = checkVCS( sourceDirectory )

	print( "-- Using repository information: revision={0} isTagged={1}".format( repositoryRevision, isTagged ) )

	if "generate-cpack" in steps:
		cpackConfigurationGenerator = CPackGenerateConfiguration( project, version, buildDirectory, repositoryRevision,
								    isTaggedRevision = isTagged )
		cpackConfigurationGenerator.run()

	if "generate-configure" in steps:
		configureScriptGenerator = ConfigureScriptGenerator( project, sourceDirectory, version )
		configureScriptGenerator.run()

	includePath = os.path.join( sourceDirectory, "include" )
	srcPath = os.path.join( sourceDirectory, "src" )

	if subprojects and "generate-cpack" in steps:
		forwardHeaderGenerator = ForwardHeaderGenerator( 
			copy = True, path = sourceDirectory, includepath = includePath, srcpath = srcPath,
			project = project, subprojects = subprojects, prefix = installPrefix, prefixed = prefixed,
			additionalHeaders = forwardHeaderMap			
		)
		forwardHeaderGenerator.run()

	print( "-- Auto-generation done." )

	with file( ".license.accepted", 'a' ):
		os.utime( ".license.accepted", None )
	print( "-- License marked as accepted." )

	print( "-- Wrote build files to: {0}".format( buildDirectory ) )
	print( "-- Now running configure script." )
	print( "" )
	sys.stdout.flush()

	configureFile = 'configure.bat' if sys.platform == 'win32' else 'configure.sh'
	configurePath = os.path.join( sourceDirectory, configureFile )
	os.execvp( configurePath, [configurePath] + sys.argv[1:] )

def policyVersion():
	global __policyVersion
	return __policyVersion
