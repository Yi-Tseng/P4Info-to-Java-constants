#!/usr/bin/env python2.7
import sys
import p4info_pb2 as proto
import google.protobuf.text_format as tf
import re

copyright = '''
/*
 * Copyright 2017-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
'''

imports = '''
import org.onosproject.net.pi.model.PiActionId;
import org.onosproject.net.pi.model.PiActionParamId;
import org.onosproject.net.pi.model.PiActionProfileId;
import org.onosproject.net.pi.model.PiControlMetadataId;
import org.onosproject.net.pi.model.PiCounterId;
import org.onosproject.net.pi.model.PiMatchFieldId;
import org.onosproject.net.pi.model.PiTableId;
'''

PKG_FMT = 'package org.onosproject.pipelines.%s;'

CLASS_OPEN = 'public final class %s {'
CLASS_CLOSE = '}'

DEFAULT_CONSTRUCTOR = '''
    // hide default constructor
    private %s() {
    }
'''

DOT = '''    public static final String DOT = ".";'''
HDR = '''    public static final String HDR = "hdr";'''

CONST_FMT = '    public static final %s %s = %s;'
SHORT_CONST_FMT ='''    public static final %s %s =
            %s;'''
JAVA_STR = 'String'
EMPTY_STR = ''
JAVA_DOC_FMT = '''/**
 * Constants for %s pipeline.
 */'''

BUILD_PI_MATCH_FIELD_FUNC = '''    private static PiMatchFieldId buildPiMatchField(String header, String field, boolean withHdrPrefix) {
        if (withHdrPrefix) {
            return PiMatchFieldId.of(HDR + DOT + header + DOT + field);
        } else {
            return PiMatchFieldId.of(header + DOT + field);
        }
    }
'''

PI_HF_FIELD_ID = 'PiMatchFieldId'
PI_HF_FIELD_ID_CST = 'buildPiMatchField(%s, "%s", %s)'
PI_HF_ID_NAME = 'HF_%s_%s_ID'
PI_HF_ID_NH_NAME = 'HF_%s_ID' # no header

PI_TBL_ID = 'PiTableId'
PI_TBL_ID_CST = 'PiTableId.of("%s")'
PI_TBL_ID_NAME = 'TBL_%s_ID'

PI_CTR_ID = 'PiCounterId'
PI_CTR_ID_CST = 'PiCounterId.of("%s")'
PI_CTR_ID_NAME = 'CNT_%s_ID'
PI_DIR_CTR_ID_CST = 'PiCounterId.of("%s")'

PI_ACT_ID = 'PiActionId'
PI_ACT_ID_CST = 'PiActionId.of("%s")'
PI_ACT_ID_NAME = 'ACT_%s_ID'

PI_ACT_PRM_ID = 'PiActionParamId'
PI_ACT_PRM_ID_CST = 'PiActionParamId.of("%s")'
PI_ACT_PRM_ID_NAME = 'ACT_PRM_%s_ID'

PI_ACT_PROF_ID = 'PiActionProfileId'
PI_ACT_PROF_ID_CST = 'PiActionProfileId.of("%s")'
PI_ACT_PROF_ID_NAME = 'ACT_PRF_%s_ID'

PI_PKT_META_ID = 'PiControlMetadataId'
PI_PKT_META_ID_CST = 'PiControlMetadataId.of("%s")'
PI_PKT_META_ID_NAME = 'CTRL_META_%s_ID'

class ConstantClassGenerator(object):
    headers = set()
    header_fields = set()
    tables = set()
    counters = set()
    direct_counters = set()
    actions = set()
    action_params = set()
    action_profiles = set()
    packet_metadata = set()

    def __init__(self, base_name):

        self.class_name = (base_name if base_name[0].isupper() else  base_name.title()) + 'Constants'
        self.package_name = PKG_FMT % (base_name.lower(), )
        self.java_doc = JAVA_DOC_FMT % (base_name, )

    def strip_control_name(self, name):
        name = name.split('.')[-1]
        name = EMPTY_STR.join(name)
        return name

    def parse(self, p4info):
        for tbl in p4info.tables:
            for mf in tbl.match_fields:
                self.header_fields.add(mf.name)
                header_name = mf.name.split('.')[-2:-1]
                header_name = EMPTY_STR.join(header_name)
                if (len(header_name) != 0):
                    self.headers.add(header_name)

            self.tables.add(tbl.preamble.name)

        for ctr in p4info.counters:
            self.counters.add(ctr.preamble.name)

        for dir_ctr in p4info.direct_counters:
            self.direct_counters.add(dir_ctr.preamble.name)

        for act in p4info.actions:
            self.actions.add(act.preamble.name)

            for param in act.params:
                self.action_params.add(param.name)

        for act_prof in p4info.action_profiles:
            self.action_profiles.add(act_prof.preamble.name)

        for cpm in p4info.controller_packet_metadata:
            for mta in cpm.metadata:
                self.packet_metadata.add(mta.name)

    def const_line(self, type, name, value):
        line = CONST_FMT % (type, name, value)
        if len(line) > 80:
            line = SHORT_CONST_FMT % (type, name, value)
        return line

    def __str__(self):
        lines = list()
        lines.append(copyright)
        lines.append(self.package_name)
        lines.append(imports)
        lines.append(self.java_doc)
        # generate the class
        lines.append(CLASS_OPEN % (self.class_name, ))
        lines.append(DEFAULT_CONSTRUCTOR % (self.class_name, ))
        if (constants_in):
            lines.append(constants_in)
        lines.append(DOT)
        lines.append('    // Header IDs')
        lines.append(HDR);
        for hdr in self.headers:
            lines.append(self.const_line(JAVA_STR, hdr.upper(), '"' + hdr + '"'))
        lines.append(EMPTY_STR)

        lines.append('    // Header field IDs')
        for hf in self.header_fields:
            splitted = hf.split('.')
            header_name = splitted[-2:-1]
            header_name = ''.join(header_name)
            header_name = header_name.upper()
            field_name = hf.split('.')[-1]
            with_hdr_prefix = 'true' if splitted[0] == 'hdr' else 'false'

            # field = hf.split('.')[1]
            if len(header_name) == 0:
                header_name = '""'
                field_var_name = PI_HF_ID_NH_NAME % (field_name.upper())
            else:
                field_var_name = PI_HF_ID_NAME % (header_name, field_name.upper())
            field_cst = PI_HF_FIELD_ID_CST % (header_name, field_name, with_hdr_prefix)
            lines.append(self.const_line(PI_HF_FIELD_ID, field_var_name, field_cst))
        lines.append(EMPTY_STR)
        lines.append(BUILD_PI_MATCH_FIELD_FUNC)

        lines.append('    // Table IDs')
        for tbl in self.tables:
            tbl_var_name = self.strip_control_name(tbl)
            tbl_var_name = PI_TBL_ID_NAME % (tbl_var_name.upper(), )
            tbl_cst = PI_TBL_ID_CST % (tbl, )

            lines.append(self.const_line(PI_TBL_ID, tbl_var_name, tbl_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Indirect Counter IDs')
        for ctr in self.counters:
            ctr_var_name = self.strip_control_name(ctr)
            ctr_var_name = PI_CTR_ID_NAME % (ctr_var_name.upper(), )
            ctr_cst = PI_CTR_ID_CST % (ctr, )
            lines.append(self.const_line(PI_CTR_ID, ctr_var_name, ctr_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Direct Counter IDs')
        for ctr in self.direct_counters:
            ctr_var_name = self.strip_control_name(ctr)
            ctr_var_name = PI_CTR_ID_NAME % (ctr_var_name.upper(), )
            ctr_cst = PI_DIR_CTR_ID_CST % (ctr, )
            lines.append(self.const_line(PI_CTR_ID, ctr_var_name, ctr_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Action IDs')
        for act in self.actions:
            # don't strip block name because we might have multiple action
            # with same name in different block (e.g. drop)
            act_var_name = act.replace('.', '_')
            act_var_name = PI_ACT_ID_NAME % (act_var_name.upper())
            act_cst = PI_ACT_ID_CST % (act, )
            lines.append(self.const_line(PI_ACT_ID, act_var_name, act_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Action Param IDs')
        for pam in self.action_params:
            pam_var_name = PI_ACT_PRM_ID_NAME % (pam.upper(), )
            pam_cst = PI_ACT_PRM_ID_CST % (pam, )
            lines.append(self.const_line(PI_ACT_PRM_ID, pam_var_name, pam_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Action Profile IDs')
        for act_prof in self.action_profiles:
            act_prof_var_name = PI_ACT_PROF_ID_NAME % (act_prof.upper().replace('.', '_'))
            act_prof_cst = PI_ACT_PROF_ID_CST % (act_prof, )
            lines.append(self.const_line(PI_ACT_PROF_ID, act_prof_var_name, act_prof_cst))
        lines.append(EMPTY_STR)

        lines.append('    // Packet Metadata IDs')
        for pkt_meta in self.packet_metadata:
            pkt_meta_var_name = PI_PKT_META_ID_NAME % (pkt_meta.upper())
            pkt_meta_cst = PI_PKT_META_ID_CST % (pkt_meta, )
            lines.append(self.const_line(PI_PKT_META_ID, pkt_meta_var_name, pkt_meta_cst))

        lines.append(CLASS_CLOSE)
        # end of class

        return '\n'.join(lines)

# removes control block name from a name of element
# e.g. ingress.table0 -> table0


def main():
    if (len(sys.argv) < 3):
        print('Usage: gen_constants.py BaseName P4InfoFile [CopyrightAndConstantsFile]')
        sys.exit(1)
    base_name = sys.argv[1]
    file_name = sys.argv[2]
    p4info = proto.P4Info()
    with open(file_name) as f:
        s = f.read()
        tf.Merge(s, p4info)

    global copyright, constants_in
    constants_in = None
    if (len(sys.argv) == 4):
        with open(sys.argv[3]) as in_file:
            other_input = re.search('^(\s*/\*.*?\*/)?(?:\s*\n)?(.*?)\s*$', in_file.read(), re.DOTALL)
            if (not other_input):
                print('File ' + sys.argv[3] +' has invalid sytax')
                sys.exit(1)
            if (other_input.group(1)):
                copyright = other_input.group(1) + "\n"
            constants_in = other_input.group(2) + "\n"

    gen = ConstantClassGenerator(base_name)
    gen.parse(p4info)
    print(gen)

if __name__ == '__main__':
    main()
