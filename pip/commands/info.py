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
                self.show_release_data(release)

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
        good_releases = [r for r in releases if r in req]
        if not good_releases:
            logger.debug('Oops, none of %r are in %r', releases, req)
            raise DistributionNotFound()

        logger.debug('Yay, %r are in %r', good_releases, req)
        raw_ver_for_parsed_ver = dict((pkg_resources.parse_version(r), r)
            for r in good_releases)
        parsed_versions = sorted(raw_ver_for_parsed_ver.keys())
        best_version = parsed_versions.pop(-1)
        logger.debug('Best of %r is %r', parsed_versions, best_version)

        best_raw_version = raw_ver_for_parsed_ver[best_version]
        logger.debug('Yay, asking for %r %r', req.project_name, best_raw_version)
        release = server.release_data(req.project_name, best_raw_version)

        release['_pip_other_versions'] = [v for v in releases if v != best_raw_version]
        logger.debug('Other versions are %r', release['_pip_other_versions'])

        return release

    def show_release_data(self, data):
        lines = list()
        lines.append("%(name)s %(version)s - %(summary)s")

        if data['author'] and data['author_email']:
            lines.append("Author: %(author)s <%(author_email)s>")
        elif data['author']:
            lines.append("Author: %(author)s")
        if data['maintainer'] and data['maintainer_email']:
            lines.append("Maintainer: %(maintainer)s <%(maintainer_email)s>")
        elif data['maintainer']:
            lines.append("Maintainer: %(maintainer)s")

        if data['home_page']:
            lines.append("Home page: %(home_page)s")
        lines.append("License: %(license)s")

        for line in lines:
            print line % data

        # These are lists, so print them directly.
        if data['provides']:
            print "Provides: %s" % ', '.join(data['provides'])
        if data['requires']:
            print "Requires: %s" % ', '.join(data['requires'])
        if data['obsoletes']:
            print "Obsoletes: %s" % ', '.join(data['obsoletes'])
        if data['_pip_other_versions']:
            print "Other versions: %s" % ', '.join(data['_pip_other_versions'])

InfoCommand()
