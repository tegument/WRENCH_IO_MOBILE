import json
import logging
import sys
import shutil

from build import ConfigurationError
from lib import task, BASE_EXCEPTION

log = logging.getLogger(__name__)

class MigrationError(BASE_EXCEPTION):
	pass

@task
def migrate_config(build):
	from_platform_version = "v1.2"
	to_platform_version = "v1.3"
	from_config_version = "1"
	to_config_version = "2"

	# Check platform version
	if build.config['platform_version'] != from_platform_version:
		raise MigrationError("'platform_version' in your src/config.json file is not set to '"+from_platform_version+"'\nThis could mean you have already migrated, in which case you can run a build as normal, or it could mean your platform version is set to a specific minor version or custom version.\n\nIf you are not sure how to proceed contact support@trigger.io.")
	
	# Check config version
	if "config_version" in build.config and build.config["from_config_version"] != 1:
		raise MigrationError("Config file version was expected to be: "+from_config_version+" however it was not.\n\nIf you are not sure how to proceed contact support@trigger.io.")
	
	# Prompt
	interactive = build.tool_config.get('general.interactive', True)
	if interactive:
		resp = raw_input("Your app will be migrated from platform version: "+from_platform_version+" to: "+to_platform_version+".\n\nThis migration will automatically update your 'src/config.json' file, further details are available from http://current-docs.trigger.io/release-notes.html\n\nPlease enter 'y' to continue or anything else to cancel:\n")
		if resp.lower() != "y":
			raise MigrationError("User cancelled migration")
			return

	
	# Regenerate config
	def copy_if_exists(key, from_dict, to_dict):
		if key in from_dict:
			to_dict[key] = from_dict[key]
			
	def generate_icons(target, sizes, from_dict, to_dict):
		new_target = {}
		for size in sizes:
			if target in from_dict['icons'] and size in from_dict['icons'][target]:
				new_target[size] = from_dict['icons'][target][size]
			elif size in from_dict['icons']:
				new_target[size] = from_dict['icons'][size]
		
		# Only save the icons if we have all the required sizes, else we'll cause a build failure
		if len(sizes) == len(new_target):
			to_dict['icons'][target] = new_target
	
	new_config = {}

	# Add basic options
	new_config['config_version'] = to_config_version
	new_config['name'] = build.config['name']
	new_config['author'] = build.config['author']
	copy_if_exists('description', build.config, new_config)
	new_config['platform_version'] = to_platform_version
	new_config['version'] = build.config['version']
	copy_if_exists('homepage', build.config, new_config)

	# Copy partners
	copy_if_exists('partners', build.config, new_config)
	
	# Add default set of modules
	new_config['modules'] = {
		"contact": True,
		"event": True,
		"file": True,
		"geolocation": True,
		"is": True,
		"logging": {
			"level": "INFO"
		},
		"message": True,
		"notification": True,
		"prefs": True,
		"request": {
			"permissions": []
		},
		"sms": True,
		"tabs": True,
		"tools": True
	}
	# Add any current modules
	if "modules" in build.config:
		for module in build.config["modules"]:
			new_config["modules"][module] = build.config["modules"][module]

	# Add any custom module config from old config
	copy_if_exists('update_url', build.config, new_config["modules"])
	copy_if_exists('parameters', build.config, new_config["modules"])
	copy_if_exists('package_names', build.config, new_config["modules"])
	copy_if_exists('logging', build.config, new_config["modules"])
	copy_if_exists('orientations', build.config, new_config["modules"])
	
	if "activations" in build.config and len(build.config['activations']) != 0:
		new_config['modules']['activations'] = build.config['activations']
	if "background_files" in build.config and len(build.config['background_files']) != 0:
		new_config['modules']['background'] = { "files": build.config['background_files'] }
	if "browser_action" in build.config:
		new_config['modules']['button'] = build.config['browser_action']
	if "libs" in build.config and "gmail" in build.config["libs"]:
		new_config['modules']['gmail'] = True
	if "libs" in build.config and "jquery" in build.config["libs"]:
		new_config['modules']['jquery'] = build.config["libs"]["jquery"]
	if "launch_images" in build.config:
		new_config['modules']['launchimage'] = build.config['launch_images']
	if "permissions" in build.config:
		perms = build.config['permissions']
		if "tabs" in perms:
			perms.remove("tabs")
		if "notifications" in perms:
			perms.remove("notifications")
		new_config['modules']['request']['permissions'] = perms

	# Migrate icons
	if "icons" in build.config:
		new_config["modules"]['icons'] = {};
		generate_icons('android', ['36', '48', '72'], build.config, new_config["modules"])
		generate_icons('chrome', ['16', '48', '128'], build.config, new_config["modules"])
		generate_icons('firefox', ['32', '64'], build.config, new_config["modules"])
		generate_icons('ios', ['57', '72', '114', '512'], build.config, new_config["modules"])
		generate_icons('safari', ['32', '48', '64'], build.config, new_config["modules"])
	
	# Backup config file
	shutil.copy2('src/config.json', 'src/config.json.bak')
	
	# Output new config
	new_config_str = json.dumps(new_config, indent=4, sort_keys=True).replace("    ", "\t")
	f = open('src/config.json', 'w')
	f.write(new_config_str)
	f.close()
	
	log.info("Migration complete, you should now be able to build as normal with the new platform version, see http://current-docs.trigger.io/release-notes.html for details of the changes made.")