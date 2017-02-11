from logging import StreamHandler, Formatter, getLogger, DEBUG, ERROR, basicConfig, root
from argparse import ArgumentParser
from .client import SimpleClient, log as client_log
from . import console_handler


# setup logging
log = getLogger(__name__)


def main():
    parser = ArgumentParser(description='Secure document exchange.')
    parser.add_argument(
        '-u',
        '--user',
        required=True,
        help='User name'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Service URL'
    )
    parser.add_argument(
        '-a',
        '--api-key',
        required=True,
        help='User\'s API key'
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

    args = vars(parser.parse_args())
    if args['debug']:
        log.setLevel(DEBUG)
        client_log.setLevel(DEBUG)
        console_handler.setLevel(DEBUG)
    log.debug('Parser args: {args}'.format(args=args))

    if args['content_type'] is None:
        client = SimpleClient.create(args['url'], args['user'], args['api_key'])
    else:
        client = SimpleClient.create(args['url'], args['user'], args['api_key'], args['content_type'])
    if args['sub_parser_name'] is None:
        parser.print_usage()
    elif args['sub_parser_name'] == 'upload':
        output = client.upload_file(args['filename'])
        print('Document ID: {output}'.format(output=output))
    elif args['sub_parser_name'] == 'download':
        output = client.download_file(args['document_id'], args['filename'], args['path'])
        if output:
            print('Successful downloaded file {filename}.'.format(filename=args['filename']))
        else:
            print('File not downloaded for document id {document_id}.'.format(document_id=args['document_id']))

if __name__ == '__main__':
    main()
