import urllib, json, sys, os, md5, subprocess

api_key = '99e53d8f451c41af9279f12ab3215168'
query = ' '.join(sys.argv[1:])
cache_dir = os.environ.get('alfred_workflow_cache', './imgs')
queue_pid = cache_dir + '/pid'
missing_images = []

def FormatItems(item):
	icon = item['images']['fixed_height_small_still']['url']
	icon_hash = md5.new(icon).hexdigest()
	icon_path = cache_dir + '/' + icon_hash

	if not os.path.isfile(icon_path):
		missing_images.append(icon)
		icon_path = None

	return {
		'title': item['slug'],
		'arg': item['bitly_gif_url'],
		'quicklookurl': item['embed_url'],
		'icon': {
			'path': icon_path
		},
		'mods': {
			'cmd': {
				'arg': item['bitly_gif_url'],
				'subtitle': 'Open in browser'
			}
		}
	}

def queue_in_progress():
	if os.path.exists(queue_pid):
		with open(queue_pid, 'r') as file:
			pid = file.read()
		try:
			subprocess.check_output(['ps', '-p', pid])
			return True
		except subprocess.CalledProcessError as e:
			output = e.output
			return False

def generate_thumbnails():
	if not missing_images:
		return False

	cmd = ['/usr/bin/curl', '--create-dirs']

	for img_path in missing_images:
		thumbnail_path = cache_dir + '/' + md5.new(img_path).hexdigest()
		cmd += ['-o', thumbnail_path, img_path]

	if not queue_in_progress():
		with open(os.devnull, 'w') as devnull:
			process = subprocess.Popen(cmd, stdout=devnull, stderr=devnull)

		# Write PID file
		with open(queue_pid, 'w') as pidfile:
			pidfile.write(str(process.pid))




if '.' not in query:
	if os.path.exists(cache_dir):
		os.system('rm -rf "{}"'.format(cache_dir))

	feedback = {
		'items': [{
			'title': 'Search Giphy for: {}'.format(query),
			'valid': False,
			'autocomplete': '{}.'.format(query)
		}]
	}
	print json.dumps(feedback)

else:

	query_string = urllib.urlencode({ 'q': query.replace('.', ''), 'api_key': api_key })
	uri = 'http://api.giphy.com/v1/gifs/search?{}'.format(query_string)
	data = json.loads(urllib.urlopen(uri).read())

	if data['meta']['status'] == 200:
		feedback = {}
		items = map(FormatItems, data['data'])
		if missing_images:
			if not os.path.exists(cache_dir):
				os.makedirs(cache_dir)
			generate_thumbnails()
			feedback['rerun'] = 1
		else:
			os.system('find {} -type f -name pid -delete'.format(cache_dir))

		feedback['items'] = items

		print json.dumps(feedback)

raise SystemExit()
