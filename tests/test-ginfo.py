#!/usr/bin/env python3

import os
import subprocess
import time
import unittest

result = {}
host = "localhost"
port = "2170"

help_message = """
Usage: ginfo [options] [Object(s)] [attribute(s)_to_filter='value of the attribute'] [attribute(s)_to_display]

List attributes corresponding to one or multiple object(s).
By default, all the attributes of an object are displayed.

[OPTIONS]
-H, --host      host        Specify a host to query. By default the
                            environmental variable LCG_GFAL_INFOSYS will be
                            used.
-b, --bind      binding     Specify the binding (o=glue by default).
-l, --list      value       List all the possible values of the specified
                            attribute or the corresponding attributes of
                            an object.
-j, --json                  Output in JSON format
-t, --timeout               Change the ldap timeout (15 seconds by default).
-v, --verbose               Enable verbose mode
-V, --version               Print the version of ginfo
-h, --help                  Print this helpful message

[OBJECTS AND CORRESPONDING ATTRIBUTES]
    AccessPolicy:
            ID, Name, Scheme, Rule, EndpointID.
    AdminDomain:
            ID, Description.
    ComputingManager:
            ID, ProductName, ProductVersion, ServiceID.
    ComputingShare:
            ID, MaxCPUTime, MaxWallTime, ServingState, RunningJobs,
            WaitingJobs, ExecutionEnvironmentID, EndpointID, Other.
    Endpoint:
            ID, URL, Capability, InterfaceName, InterfaceVersion,
            Implementor, ImplementationVersion, QualityLevel, HealthState,
            ServingState, ServiceID.
    ExecutionEnvironment:
            ID, OSName, ConnectivityOut, MainMemorySize, VirtualMemorySize.
    Location:
            ID, Country, Latitude, Longitude.
    MappingPolicy:
            ID, Scheme, Rule, ShareID.
    Service:
            ID, Capability, Type, QualityLevel, StatusInfo, DomainID.
    Share:
            ID, ServiceID.
    StorageShare:
            ID, SharingID, Path, AccessMode, AccessLatency, ServingState,
            RetentionPolicy, ExpirationMode, DefaultLifeTime,
            MaximumLifeTime, Tag.

"""  # noqa: E501

list_message = """Available attributes are:

        cap       EndpointCapability
        domain    ServiceAdminDomainForeignKey
        id        ServiceID
        imp       EndpointImplementationName
        impv      EndpointImplementationVersion
        int       EndpointInterfaceName
        intv      EndpointInterfaceVersion
        ql        EndpointQualityLevel
        type      ServiceType
        url       EndpointURL
        vo        PolicyRule"""

host_message = "The following host will be used: " + host

version_message = "ginfo V1.9.0"

normal_output = "EndpointCapability: capability_a, capability_b, capability_c\nServiceAdminDomainForeignKey: domain_a\nServiceID: service_1\nEndpointImplementationName: implementation_name_a\nEndpointImplementationVersion: 5.0.0\nEndpointInterfaceName: interface_name_a\nEndpointInterfaceVersion: 3.0.0\nEndpointQualityLevel: testing\nServiceType: service_type_a\nEndpointURL: ldap://host:2170/XXX\nPolicyRule: ALL\n"

json_output = '{"service_1": {"EndpointImplementationVersion": "5.0.0", "ServiceAdminDomainForeignKey": "domain_a", "EndpointQualityLevel": "testing", "EndpointInterfaceVersion": "3.0.0", "EndpointImplementationName": "implementation_name_a", "PolicyRule": ["ALL"], "EndpointURL": "ldap://host:2170/XXX", "EndpointCapability": ["capability_a", "capability_b", "capability_c"], "ServiceID": "service_1", "EndpointInterfaceName": "interface_name_a", "ServiceType": "service_type_a"}}'

csv_output = 'EndpointCapability,ServiceAdminDomainForeignKey,ServiceID,EndpointImplementationName,EndpointImplementationVersion,EndpointInterfaceName,EndpointInterfaceVersion,EndpointQualityLevel,ServiceType,EndpointURL,PolicyRule\n"capability_a,capability_b,capability_c",domain_a,service_1,implementation_name_a,5.0.0,interface_name_a,3.0.0,testing,service_type_a,ldap://host:2170/XXX,"ALL"'

emi_output = [
    "[",
    '"Service_Type": "service_type_a"',
    '"Endpoint_Capability": ["capability_a"',
    '"capability_b"',
    '"capability_c"]',
    '"Endpoint_Interface_Name": "interface_name_a"',
    '"Endpoint_Implementation_Name": "implementation_name_a"',
    '"Service_Endpoint_URL": "ldap://host:2170/XXX"',
    '"Endpoint_Interface_Version": "3.0.0"',
    '"Service_Id": "service_1"',
    '"Endpoint_Implementation_Version": "5.0.0"',
    '"Service_Admin_Domain": "domain_a"',
    '"Endpoint_Quality_Level": "testing"',
    "]",
]

list_results = {
    "cap": [
        None,
        "EndpointCapability",
        {
            "capability_a": ["service_1", "service_4"],
            "capability_b": ["service_1", "service_3"],
            "capability_c": ["service_1"],
            "capability_d": ["service_2", "service_4"],
            "capability_e": ["service_3"],
        },
        [
            'service_4,"capability_a,capability_d"',
            'service_1,"capability_a,capability_b,capability_c"',
            'service_3,"capability_b,capability_e"',
            'service_2,"capability_d"',
        ],
    ],
    "domain": [
        "d",
        "ServiceAdminDomainForeignKey",
        {
            "domain_a": ["service_1", "service_2"],
            "domain_b": ["service_3"],
            "": ["service_4"],
        },
    ],
    "id": [
        "i",
        "ServiceID",
        {
            "service_1": ["service_1"],
            "service_2": ["service_2"],
            "service_3": ["service_3"],
            "service_4": ["service_4"],
        },
    ],
    "imp": [
        "m",
        "EndpointImplementationName",
        {
            "implementation_name_a": ["service_1"],
            "implementation_name_b": ["service_2", "service_3"],
            "implementation name c": ["service_4"],
        },
    ],
    "impv": [
        None,
        "EndpointImplementationVersion",
        {
            "5.0.0": ["service_1", "service_3"],
            "5.0.1": ["service_2"],
            "NotANumber": ["service_4"],
        },
    ],
    "int": [
        "n",
        "EndpointInterfaceName",
        {
            "interface_name_a": ["service_1", "service_4"],
            "interface_name_b": ["service_2", "service_3"],
        },
    ],
    "intv": [
        None,
        "EndpointInterfaceVersion",
        {
            "3.0.0": ["service_1"],
            "3.0.1": ["service_2", "service_3"],
            "NotANumber": ["service_4"],
        },
    ],
    "ql": [
        "q",
        "EndpointQualityLevel",
        {
            "testing": ["service_1", "service_2"],
            "production": ["service_3"],
            "OtherQuality": ["service_4"],
        },
    ],
    "type": [
        "t",
        "ServiceType",
        {
            "service_type_a": ["service_1", "service_3"],
            "service_type_b": ["service_2", "service_4"],
        },
    ],
    "url": [
        "u",
        "EndpointURL",
        {
            "ldap://host:2170/XXX": ["service_1"],
            "ldap://host:2170/YYY": ["service_2"],
            "ldap://host:2170/ZZZ": ["service_3"],
            "host:2170/AAA": ["service_4"],
        },
    ],
    "vo": [
        None,
        "PolicyRule",
        {
            "ALL": ["service_1", "service_2"],
            "VO:cms": ["service_1", "service_2"],
            "VO:atlas": ["service_1", "service_2", "service_3"],
            "INVALID": ["service_1", "service_2"],
        },
        [
            'service_4,"INVALID"',
            'service_1,"ALL"',
            'service_3,"VO:atlas"',
            'service_2,"ALL,VO:cms"',
        ],
    ],
}


class TestGinfo(unittest.TestCase):
    def assert_equal(self, command, string, error=None):
        if command not in result:
            result[command] = subprocess.getstatusoutput(command)[1]
        if not error:
            error = "Error"
        error += (
            " - command: '"
            + command
            + "'\n'"
            + str(result[command])
            + "'\n\n!=\n\n'"
            + str(string)
            + "'"
        )
        self.assertEqual(result[command], string, error)

    def assert_regexp_matches(self, command, string, error=None):
        if command not in result:
            result[command] = subprocess.getstatusoutput(command)[1]
        if not error:
            error = "Error"
        error += " - command: '" + command + "'"
        self.assertRegex(result[command], string, error)

    def assert_not_regexp_matches(self, command, string, error=None):
        if command not in result:
            result[command] = subprocess.getstatusoutput(command)[1]
        if not error:
            error = "Error"
        error += " - command: '" + command + "'"
        self.assertNotRegexpMatches(result[command], string, error)

    def assert_items_equal(self, command, expected_items, error=None):
        if command not in result:
            result[command] = subprocess.getstatusoutput(command)[1]
        if not error:
            error = "Error"
        res = result[command].split("\n\n", 1)
        i = len(res) - 1
        res.extend(res[i].split("\n"))
        res.remove(res[i])
        error += (
            " - command: '"
            + command
            + "'\n"
            + str(res)
            + "\n\n!=\n\n"
            + str(expected_items)
        )
        self.assertItemsEqual(res, expected_items, error)

    def assert_items_equal2(self, command, expected_items, error=None):
        if command not in result:
            result[command] = subprocess.getstatusoutput(command)[1]
        if not error:
            error = "Error"
        res = result[command].split("{", 1)
        res.extend(res[1].split(", "))
        res.remove(res[1])
        res.extend(res[-1].split("}"))
        res.remove(res[-3])
        error += (
            " - command: '"
            + command
            + "'\n"
            + str(res)
            + "\n\n!=\n\n"
            + str(expected_items)
        )
        self.assertItemsEqual(res, expected_items, error)

    def assert_time_equal(self, command, expected_time):
        start_time = time.time()
        result[command] = subprocess.getstatusoutput(command)[1]
        duration = "%d" % (time.time() - start_time)
        self.assertEqual(duration, expected_time)

    @unittest.skip("Not really meaningful")
    def test1_messages(self):
        tests = [
            ("-h", help_message),
            ("--help", help_message),
            ("-l", list_message),
            ("--list", list_message),
            ("-V", version_message),
            ("--version", version_message),
        ]
        for i, j in tests:
            self.assert_equal("ginfo " + i, j)

    @unittest.skip("Not really meaningful")
    def test2_bdii(self):
        self.assert_regexp_matches(
            "unset LCG_GFAL_INFOSYS;ginfo --host " + host + " -v", host_message
        )
        self.assert_equal("unset LCG_GFAL_INFOSYS;ginfo", help_message)
        self.assert_not_regexp_matches(
            "export LCG_GFAL_INFOSYS='" + host + ":" + port + "';ginfo", help_message
        )

    @unittest.skip("Broken, -i parameter for ServiceID does not exist")
    def test3_output(self):
        tests = [
            ("", normal_output),
            ("-j", json_output),
            ("--json", json_output),
            ("-c", csv_output),
            ("--csv", csv_output),
        ]
        tests2 = [("-e", emi_output), ("--emi", emi_output)]
        for i, j in tests:
            print("ginfo -i service_1 %s" % i)
            self.assert_equal("ginfo -i service_1 " + i, j)
        for i, j in tests2:
            self.assert_items_equal2("ginfo -i service_1 " + i, j)

    @unittest.skip("Broken")
    def test4_list_attr(self):
        for i in ("-l", "--list"):
            for j in list_results:
                expected_items = [
                    "Verbose mode enabled\nThe following host will be used: "
                    + host
                    + ":"
                    + port
                    + "\nList all the possible values for the following attribute: "
                    + list_results[j][1]
                ]
                expected_items.extend(list_results[j][2].keys())
                self.assert_items_equal("ginfo -v " + i + " " + j, expected_items)

    @unittest.skip("Broken")
    def test5_filter_attr(self):
        for att in list_results:
            if list_results[att][0]:
                opts = ("--" + att, "-" + list_results[att][0])
            else:
                opts = ("--" + att,)
            for i in opts:
                for j in list_results[att][2]:
                    if j and j.find(" ") == -1:
                        expected_items = [
                            "Verbose mode enabled\nOutput in csv formating\nThe following host will be used: "
                            + host
                            + ":"
                            + port
                            + "\nFilter services by the following "
                            + list_results[att][1]
                            + ": "
                            + j
                            + "\nThe following attribute(s) will be displayed: ServiceID"
                        ]
                        expected_items.append("ServiceID")
                        expected_items.extend(list_results[att][2][j])
                        self.assert_items_equal(
                            "ginfo -c " + i + " " + j + " -v id", expected_items
                        )

    @unittest.skip("Broken")
    def test6_display_attr(self):
        for att in list_results:
            for i in (att, list_results[att][1]):
                if i not in ["id", "ServiceID"]:
                    expected_items = [
                        "Verbose mode enabled\nOutput in csv formating\nThe following host will be used: "
                        + host
                        + ":"
                        + port
                        + "\nThe following attribute(s) will be displayed: ServiceID "
                        + list_results[att][1]
                    ]
                    expected_items.append("ServiceID," + list_results[att][1])
                    if att in ["cap", "vo"]:
                        expected_items.extend(list_results[att][3])
                    else:
                        for j in list_results[att][2]:
                            for k in range(len(list_results[att][2][j])):
                                expected_items.append(
                                    list_results[att][2][j][k] + "," + j
                                )
                    self.assert_items_equal("ginfo -v -c id " + i, expected_items)

    @unittest.skip("Broken")
    def test7_cleaning(self):
        tests = [
            ("vo", 'PolicyRule\n"INVALID"'),
            (
                "--clean",
                'EndpointCapability,ServiceAdminDomainForeignKey,ServiceID,EndpointImplementationName,EndpointImplementationVersion,EndpointInterfaceName,EndpointInterfaceVersion,EndpointQualityLevel,ServiceType,EndpointURL,PolicyRule\n"capability_a,capability_d",INVALID,service_4,INVALID,INVALID,interface_name_a,INVALID,INVALID,service_type_b,INVALID,"INVALID"',
            ),
            (
                "--strict",
                'EndpointCapability,ServiceAdminDomainForeignKey,ServiceID,EndpointImplementationName,EndpointImplementationVersion,EndpointInterfaceName,EndpointInterfaceVersion,EndpointQualityLevel,ServiceType,EndpointURL,PolicyRule\n"INVALID,INVALID",INVALID,service_4,INVALID,INVALID,INVALID,INVALID,INVALID,INVALID,INVALID,"INVALID"',
            ),
        ]
        for i, j in tests:
            self.assert_equal("ginfo -c -i service_4 " + i, j)

    @unittest.skip("Broken")
    def test8_various(self):
        tests = [
            ("--cap capability_b --intv 3.0.1 id", "ServiceID\nservice_3"),
            (
                "--vo VO:cms -t service_type_b EndpointURL",
                "EndpointURL\nldap://host:2170/YYY",
            ),
            (
                "--vo VO:atlas --imp implementation_name_b -q production id intv",
                "ServiceID,EndpointInterfaceVersion\nservice_3,3.0.1",
            ),
            (
                "-d domain_a -n interface_name_a --impv 5.0.0 cap",
                'EndpointCapability\n"capability_a,capability_b,capability_c"',
            ),
            ("--id service_2 -u ldap://host:2170/ZZZ id", "ServiceID"),
            (
                "--url ldap://host:2170/ZZZ PolicyRule vo EndpointQualityLevel cap",
                'PolicyRule,EndpointQualityLevel,EndpointCapability\n"VO:atlas",production,"capability_b,capability_e"',
            ),
            (
                "-d domain_b --impv 5.0.0 -m implementation_name_b -n interface_name_b --cap capability_e --vo VO:atlas -u ldap://host:2170/ZZZ --intv 3.0.1 --ql production --type service_type_a --id service_3 id",
                "ServiceID\nservice_3",
            ),
            ("--vo ALL ServiceID", "ServiceID\nservice_1\nservice_2"),
            ("--cap capability_b --vo ALL id", "ServiceID\nservice_1"),
            ("--ql testing --type service_type_a vo", 'PolicyRule\n"ALL"'),
            (
                "--impv 5.0.* id impv",
                "ServiceID,EndpointImplementationVersion\nservice_1,5.0.0\nservice_3,5.0.0\nservice_2,5.0.1",
            ),
            (
                "-v -i service_1 --clean --timeout 5 id",
                "Verbose mode enabled\nOutput in csv formating\nThe following host will be used: localhost:2170\nResults have been cleaned.\nLdap timeout has been set to 5 second(s).\nFilter services by the following ServiceID: service_1\nThe following attribute(s) will be displayed: ServiceID\n\nServiceID\nservice_1",
            ),
            (
                "-v --strict --list domain",
                "Verbose mode enabled\nThe following host will be used: localhost:2170\nList all the possible values for the following attribute: ServiceAdminDomainForeignKey\nOption --csv is not compatible with --list option.\nResults have been cleaned strictly.\n\ndomain_a\ndomain_b\nINVALID",
            ),
        ]
        for i, j in tests:
            self.assert_equal("ginfo -c " + i, j)

    @unittest.skip("Disabled to speed up debug")
    def test9_timeout(self):
        self.assert_time_equal("ginfo --host bdii.scotgrid.ac.uk Endpoint", "60")
        self.assert_time_equal(
            "ginfo --host bdii.scotgrid.ac.uk --timeout 3 Endpoint", "3"
        )


if __name__ == "__main__":
    os.environ["LCG_GFAL_INFOSYS"] = host + ":" + port
    unittest.main()
