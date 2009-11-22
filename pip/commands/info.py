import os
import pkg_resources
import pip
from pip.log import logger
from pip.locations import build_prefix, src_prefix
from pip.basecommand import Command
from pip.exceptions import DistributionNotFound

class InfoCommand(Command):
    name = 'info'
    usage = '%prog [OPTIONS] DISTRIBUTION_NAMES...'
    summary = 'Get info from PyPI about distributions'

    def __init__(self):
        super(InfoCommand, self).__init__()

        self.parser.add_option(
            '-i', '--index-url', '--pypi-url',
            dest='index_url',
            metavar='URL',
            default='http://pypi.python.org/pypi',
            help='Base URL of Python Package Index (default %default)')
        self.parser.add_option(
            '--extra-index-url',
            dest='extra_index_urls',
            metavar='URL',
            action='append',
            default=[],
            help='Extra URLs of package indexes to use in addition to --index-url')

    def run(self, options, args):
        indexes = [options.index_url] + options.extra_index_urls

        release_data = dict()

        first_dist = True
        for dist in args:
            if first_dist:
                first_dist = False
            else:
                print

            try:
                release = self.release_in_indexes(dist, indexes)
            except DistributionNotFound:
                print "Found no such release %r" % dist
            else:
                self.show_release_data(release,
                    show_index=bool(options.extra_index_urls))

    def release_in_indexes(self, dist, indexes):
        for index_url in indexes:
            try:
                return self.release_in_index(dist, index_url)
            except DistributionNotFound:
                pass
        raise DistributionNotFound()

    def release_in_index(self, dist, index_url):
        import xmlrpclib
        server = xmlrpclib.Server(index_url)

        req = pkg_resources.Requirement.parse(dist)
        logger.debug('Requirement for %r is %r', dist, req)

        releases = server.package_releases(req.project_name)
        logger.debug('Checking if %r are in %r', releases, req)
        good_releases = sorted((r for r in releases if r in req),
            key=pkg_resources.parse_version)
        if not good_releases:
            logger.debug('Oops, none of %r are in %r', releases, req)
            raise DistributionNotFound()

        logger.debug('Yay, %r are in %r', good_releases, req)
        best_release = good_releases.pop(-1)
        logger.debug('Yay, asking for %r %r', req.project_name, best_release)
        release = server.release_data(req.project_name, best_release)

        release['_pip_index_url'] = index_url
        release['_pip_other_versions'] = [r for r in releases if r != best_release]
        logger.debug('Other versions are %r', release['_pip_other_versions'])

        return release

    def show_release_data(self, data, show_index=False):
        lines = list()
        lines.append("%(name)s %(version)s - %(summary)s")

        if data.get('author') and data.get('author_email'):
            lines.append("Author: %(author)s <%(author_email)s>")
        elif data.get('author'):
            lines.append("Author: %(author)s")
        if data.get('maintainer') and data.get('maintainer_email'):
            lines.append("Maintainer: %(maintainer)s <%(maintainer_email)s>")
        elif data.get('maintainer'):
            lines.append("Maintainer: %(maintainer)s")

        if data.get('home_page'):
            lines.append("Home page: %(home_page)s")
        if data.get('license') and data.get('license') != 'UNKNOWN':
            lines.append("License: %(license)s")

        for line in lines:
            print line % data

        # These are lists, so print them directly.
        if data.get('provides'):
            print "Provides: %s" % ', '.join(data['provides'])
        if data.get('requires'):
            print "Requires: %s" % ', '.join(data['requires'])
        if data.get('obsoletes'):
            print "Obsoletes: %s" % ', '.join(data['obsoletes'])
        if show_index:
            print "Found in index: %s" % data['_pip_index_url']
        if data['_pip_other_versions']:
            print "Other versions: %s" % ', '.join(data['_pip_other_versions'])

InfoCommand()
