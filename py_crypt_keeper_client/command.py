#   Copyright 2017 Maurice Carey
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

from logging import StreamHandler, Formatter, getLogger, DEBUG, ERROR, basicConfig, root
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from .client import SimpleClient, log as client_log
from . import console_handler
from json import dumps, loads
from sys import stdin, stderr
from os import path


# setup logging
log = getLogger(__name__)


CONFIGURATION_FILE_NAME = path.join(path.expanduser('~'), '.ckc_config.json')
REQUIRED_CONFIG = {
    'url': ('url', 'Service URL'),
    'user': ('user', 'User name'),
    'api_key': ('api-key', 'User\'s API key'),
}


def merge(override_map=None, default_map=None):
    m = dict(default_map or {})
    m.update(override_map)
    for key in m:
        if m[key] is None:
            m[key] = default_map.get(key)
    return m


def get_config(args):
    config = None
    try:
        config = loads(open(CONFIGURATION_FILE_NAME, 'r', encoding='utf-8').read())
    except IOError:
        log.warning(
            'Could not load configuration from file "{filename}". Will use command line arguments only.'
            .format(filename=CONFIGURATION_FILE_NAME)
        )
    return merge(args, config)


def validate_config(config):
    r = list()
    for k, v in REQUIRED_CONFIG.items():
        if k not in config or config[k] is None:
            r.append(v)
    if len(r) == 0:
        return None
    else:
        return r


def main():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description='Secure document exchange.',
        epilog='''
  Copyright 2017 Maurice Carey

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
        '''
    )
    parser.add_argument(
        '-u',
        '--%s' % REQUIRED_CONFIG['user'][0],
        help=REQUIRED_CONFIG['user'][1],
    )
    parser.add_argument(
        '--%s' % REQUIRED_CONFIG['url'][0],
        help=REQUIRED_CONFIG['url'][1],
    )
    parser.add_argument(
        '-a',
        '--%s' % REQUIRED_CONFIG['api_key'][0],
        help=REQUIRED_CONFIG['api_key'][1],
    )
    parser.add_argument(
        '-c',
        '--content-type',
        help='The content type of the file.'
    )
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='Set the log level to debug.',
    )
    parser.add_argument(
        '-j',
        '--json',
        action='store_true',
        help='Output json data.',
    )
    sub_parsers = parser.add_subparsers(
        title='sub-command',
        description='valid sub-commands',
        dest='sub_parser_name',
        help='sub-command help',
    )

    upload_parser = sub_parsers.add_parser('upload', help='upload help')
    upload_parser.add_argument(
        'filename',
        help='The name of the file to upload.'
    )

    download_parser = sub_parsers.add_parser('download', help='download help')
    download_parser.add_argument(
        'document_id',
        help='The document id for the document to download.'
    )
    download_parser.add_argument(
        '-f',
        '--filename',
        help='The name of the file to download.'
    )
    download_parser.add_argument(
        '-p',
        '--path',
        help='The path to the file to download.'
    )

    share_parser = sub_parsers.add_parser('share', help='share help')
    share_parser.add_argument(
        'document_id',
        help='The document id to share or lookup.'
    )
    share_parser.add_argument(
        '-a',
        '--add',
        help='The name of a user to add to document share.'
    )

    write_config_parser = sub_parsers.add_parser('write-config', help='Write supplied required args to config file.')

    args = vars(parser.parse_args())
    config = get_config(args)
    if config.get('debug'):
        log.setLevel(DEBUG)
        client_log.setLevel(DEBUG)
        console_handler.setLevel(DEBUG)
    log.debug('Parser args: {args}'.format(args=config))
    json = config['json']
    if config.get('sub_parser_name') == 'write-config':
        output_config = dict()
        for key in config:
            if key in REQUIRED_CONFIG and config[key] is not None:
                output_config[key] = config[key]
        with open(CONFIGURATION_FILE_NAME, 'w', encoding='utf-8') as config_file:
            config_file.write(dumps(output_config))
            config_file.flush()
            config_file.close()
            if json:
                print(dumps(
                    {
                        'success': True,
                        'filename': CONFIGURATION_FILE_NAME,
                    }
                ))
            else:
                print('Successfully wrote config to file: {filename}'.format(filename=CONFIGURATION_FILE_NAME))
        exit()
    valid = validate_config(config)
    if valid is not None:
        for v in valid:
            print(
                'ERROR: argument {argument_name} must be provided either on command line or via configuration file.'
                    .format(argument_name=v[0]),
                file=stderr,
            )
        parser.print_usage()
        exit()

    if config.get('content_type') is None:
        client = SimpleClient.create(config['url'], config['user'], config['api_key'])
    else:
        client = SimpleClient.create(['url'], config['user'], config['api_key'], config['content_type'])
    if config['sub_parser_name'] is None:
        parser.print_usage()
        exit()
    elif config['sub_parser_name'] == 'upload':
        output = client.upload_file(config['filename'])
        if json:
            print(dumps(
                {
                    'documentId': output,
                }
            ))
        else:
            print('Document ID: {output}'.format(output=output))
    elif config['sub_parser_name'] == 'download':
        document_id = config['document_id']
        if document_id == '-':
            document_id = None
            with stdin as f:
                document_id = loads(f.read()).get('documentId')
        if document_id is None:
            print('ERROR: Document id must be provided.', file=stderr)
            exit()
        output = client.download_file(document_id, config['filename'], config['path'])
        if json:
            print(dumps(
                {
                    'downloaded': output,
                }
            ))
        else:
            if output:
                print('Successful downloaded file {filename}.'.format(filename=config['filename']))
            else:
                print('File not downloaded for document id {document_id}.'.format(document_id=config['document_id']))
    elif config['sub_parser_name'] == 'share':
        document_id = config['document_id']
        if document_id == '-':
            document_id = None
            with stdin as f:
                document_id = loads(f.read()).get('documentId')
        if document_id is None:
            print('ERROR: Document id must be provided.', file=stderr)
            exit()
        username = config.get('add')
        if username is not None:
            output = client.post_share(document_id, username)
            if json:
                print(dumps(
                    {
                        'resource_url': output
                    }
                ))
            else:
                if output:
                    print('Successfully added {username} to {document_id}.'.format(
                        username=username,
                        document_id=document_id,
                    ))
                else:
                    print('Could not add {username} to {document_id}. See logs.'.format(
                        username=username,
                        document_id=document_id,
                    ))
        else:
            output = client.get_share(document_id)
            if json:
                print(dumps(
                    {
                        'document_id': document_id,
                        'users': output,
                    }
                ))
            else:
                print('Users {users} have access to {document_id}.'.format(
                    users=output,
                    document_id=document_id,
                ))

if __name__ == '__main__':
    main()
