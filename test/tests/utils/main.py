#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, unittest, argparse
import configuration, misc

from fabric import api, network, state
from fabric.context_managers import settings


def _pad(text, offset, pad, length):
    return '%s %s %s' % (pad * (offset - 1), text,
                         pad * (length - 2 - len(text) - offset))


def _description():
    return '%s %s' % (api.env.host_string,
                      api.env.aruba_host.vm_name)


class CloudTestResult(unittest.runner.TextTestResult):
    @property
    def separator1(self):
        return _pad(_description(), 4, '=', 70)

    @property
    def separator2(self):
        return _pad(_description(), 4, '-', 70)

    def addError(self, test, err):
        if isinstance(err[1], misc.FatalError):
            self.stop()

        super(unittest.runner.TextTestResult, self).addError(test, err)

    def addFailure(self, test, err):
        if isinstance(err[1], misc.FatalError):
            self.stop()

        super(unittest.runner.TextTestResult, self).addError(test, err)


class CloudTestRunner(object):
    def __init__(self, config, verbosity, hosts):
        self.configuration = config
        self.verbosity = verbosity
        self.hosts = hosts

    def run(self, suite):
        with settings(api.hide('running', 'stdout', 'stderr', 'user'),
                      hosts=self.hosts.keys(),
                      parallel=False):
            api.execute(self.runTests, suite)

        network.disconnect_all()

        return unittest.result.TestResult()

    def runTests(self, suite):
        api.env.aruba_configuration = self.configuration
        api.env.aruba_host = self.hosts[api.env.host_string]
        api.env.aruba_platform = api.env.aruba_host.platform
        api.env.aruba_xmlrpc_verbose = self.verbosity > 2

        if api.env.aruba_platform.os_type == 'bsd':
            api.env.shell = '/bin/sh -c'

        runner = unittest.TextTestRunner(
            resultclass=CloudTestResult,
            verbosity=self.verbosity,
        )

        return runner.run(suite)


class TestProgram(unittest.TestProgram):
    UNITTEST_ARGS = ['verbose', 'quiet', 'failfast']
    HELP_EPILOG = """
Examples:
  tests                               - run default set of tests
  tests MyTestSuite                   - run suite 'MyTestSuite'
  tests MyTestCase.testSomething      - run MyTestCase.testSomething
  tests MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
""" + ' ' # trailing space to have blank line after output

    def __init__(self, *args, **kwargs):
        self.__hosts = {}

        # this calls parseArgs and runTests
        super(TestProgram, self).__init__(*args, **kwargs)

    def parseArgs(self, argv):
        if len(argv) > 1 and argv[1].lower() == 'discover':
            super(TestProgram, self).parseArgs(argv)
            return

        # we parse unittest options here and then re-construct the
        # argv array for unittest to be able to provide the correct usage
        # information in case of errors
        parser = argparse.ArgumentParser(
            epilog=self.HELP_EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('--host', metavar='HOST', type=str, action='append',
                            nargs=1, help='Hosts that the tests will be run on')
        parser.add_argument('--list', action='store_true',
                            help='List all tests')
        parser.add_argument('--config', nargs=1, default='config/config.ini',
                            help='Path to configuration file')
        parser.add_argument('--verbose', '-v', action='count',
                            help='Verbose output (can be specified multiple times)')
        parser.add_argument('--quiet', action='store_true',
                            help='Minimal output')
        parser.add_argument('--failfast', action='store_true',
                            help='Stop on first failure')
        parser.add_argument('tests', metavar='TEST', nargs='*',
                            help='Test classes/methods to execute')

        self.__args = parser.parse_args(argv[1:])
        self.__configuration = configuration.parse(self.__args.config)

        # construct the list of hosts
        if self.__args.host:
            tests = []
            for h in self.__args.host:
                tests.extend(h)
        else:
            tests = [self.__configuration.default_test]

        for test in tests:
            if test in self.__configuration.tests:
                hosts = self.__configuration.tests[test].hosts
            elif test in self.__configuration.hosts:
                hosts = [self.__configuration.hosts[test]]
            else:
                print "'%s' is neither a configured host nor a host list" % \
                    test
                sys.exit(1)

            self.__hosts.update(dict((h.hostString, h) for h in hosts))

        # create argv for unittest' TestProgram
        super_args = ['--%s' % s for s in self.UNITTEST_ARGS
                          if getattr(self.__args, s)]

        super(TestProgram, self).parseArgs(
            argv[:1] + super_args + self.__args.tests)

        if self.__args.verbose > 0:
            self.verbosity = self.__args.verbose + 1

        if self.__args.list:
            print 'Tests:\n'
            self.__prettyPrintSuite()
            print 'Hosts:\n'
            self.__prettyPrintHosts()
            print ''
            sys.exit(0)

    def runTests(self):
        self.testRunner = CloudTestRunner(
            self.__configuration, self.verbosity,
            self.__hosts
        )

        super(TestProgram, self).runTests()

    def __prettyPrintHosts(self):
        for key, host in self.__configuration.hosts.items():
            print '%s:\n  %s' % (key, host.platform.description())

    def __prettyPrintSuite(self):
        classes = {}

        for suite in self.test:
            for test in suite:
                cls_name = test.__class__.__name__
                meth_name = test._testMethodName

                if cls_name not in classes:
                    classes[cls_name] = []

                classes[cls_name].append(meth_name)

        for cls_name in sorted(classes.keys()):
            print '- %s' % cls_name

            for meth_name in sorted(classes[cls_name]):
                print '  - %s.%s' % (cls_name, meth_name)

            print ''


main = TestProgram
