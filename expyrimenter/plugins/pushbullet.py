import requests
import json
from expyrimenter.core import Config, ExpyLogger
from os.path import getmtime, expanduser
import time


class Pushbullet:
    """ Requires ``[pushbullet]`` section with ``token`` value in config.
    Check :class:`expyrimenter.Config` for more details about configuration.
    """

    _url = 'https://api.pushbullet.com/v2/pushes'

    def __init__(self):
        self._logger = ExpyLogger.getLogger('pushbullet')

        token = Config('pushbullet').get('token')
        if token is None:
            msg = 'No pushbullet access token found. Check Config doc.'
            self._logger.critical(msg)
            raise AttributeError(msg)
        self._token = token

    def send_note(self, title='', body=''):
        """
        Sends a message using pushbullet *note* type.

        :param str title: Optional message title
        :param str body: Optional message body content
        """
        note = json.dumps({'type': 'note', 'title': title, 'body': body})
        headers = {'Content-Type': 'application/json'}
        res = requests.post(Pushbullet._url,
                            data=note,
                            headers=headers,
                            auth=(self._token, ''))

        if res.status_code == requests.codes.ok:
            self._logger.success('note sent')
        else:
            self._logger.error(res.json)

    def monitor_file(self, filename, max_mod_interval, title=None, body=None):
        """
        Sends a message if *filename* is not modified within *max_mod_interval*
        seconds. When a message is sent, it stops monitoring the file.
        Otherwise, it keeps running until it is killed.

        :param str filename: The filename to be monitored
        :param int max_mod_interval: If *filename* is not modified within
         *max_mod_interval* seconds, a message will be sent
        :param str title: Optional message title
        :param str body: Optional message body content
        """
        if title is None:
            title = filename
        if body is None:
            body = 'File not changed in {:d} seconds.'.format(max_mod_interval)
        filename = expanduser(filename)

        note_sent = False
        while not note_sent:  # one message at max
            # time since last file modification
            time_since = time.time() - getmtime(filename)
            if time_since >= max_mod_interval:
                self._logger.info('File {} not modified'.format(filename))
                self.send_note(title, body)
                note_sent = True
            else:
                # Wait until max_mod_interval after last modification
                sleep = max_mod_interval - time_since  # we know this is > 0
                time.sleep(sleep)
