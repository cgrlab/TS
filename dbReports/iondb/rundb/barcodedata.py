# Copyright (C) 2014 Ion Torrent Systems, Inc. All Rights Reserved
from __future__ import absolute_import

import json
import os
import ast
import logging
from django.conf import settings
from django.utils.functional import cached_property
from iondb.rundb.models import Results, dnaBarcode

logger = logging.getLogger(__name__)

REFERENCE = 'reference'
REFERENCE_FULL_PATH = 'reference_fullpath'
TARGET_REGION_FILEPATH = 'target_region_filepath'
TARGET_REGION_BED = 'targetRegionBedFile'
HOT_SPOT_FILE_PATH = 'hotspot_filepath'
HOT_SPOT_BED = 'hotSpotRegionBedFile'
BAM = 'bam_file'
BAM_FULL_PATH = 'bam_filepath'
NON_BARCODED = 'nonbarcoded'
NO_MATCH = 'nomatch'
BARCODE_SEQUENCE = 'barcode_sequence'
SAMPLE = 'sample'
SAMPLE_ID = 'sample_id'
FILTERED = 'filtered'
BARCODE_DESCRIPTION = 'barcode_description'
DESCRIPTION = 'description'
BARCODE_NAME = 'barcode_name'
BARCODE_INDEX = 'barcode_index'
INDEX = 'index'
READ_COUNT = 'read_count'
ALIGNED = 'aligned'
BARCODE_ADAPTER = 'barcode_adapter'
BARCODE_ANNOTATION = 'barcode_annotation'
BARCODE_SEQUENCE = 'barcode_sequence'
BARCODE_TYPE = 'barcode_type'
NUCLEOTIDE_TYPE = 'nucleotide_type'
CONTROL_SEQUENCE_TYPE = 'control_sequence_type'
GENOME_URL = 'genome_urlpath'

# TODO: for later release
#ANALYSIS_PARAMETERS = 'analysis_parameters'

class BarcodeSampleInfo(object):
    """
    Aggregate data from plan/eas barcodesample info
    and from pipeline datasets_basecaller
    Fallback gently for non-barcoded data.
    """

    def __init__(self, resultid, result=None):
        # Gather DB info
        self.result = result or Results.objects.select_related('eas').get(pk=resultid)
        self.eas = self.result.eas

    @staticmethod
    def getFullBamPath(reportFullPath, referenceGenome, bamFileName, filtered):
        """
        Helper method to find the full path of the BAM file
        :param: reportFullPath:
        :param referenceGenome:
        :param bamFileName:
        :param filtered: Boolean indicating if the item was filtered
        :return:
        """
        bamFullPath = ''
        if referenceGenome and not filtered:
            bamFullPath = os.path.join(reportFullPath, bamFileName)
        else:
            # if there is not a reference file then we need to file the basecaller bam file
            if not bamFileName.endswith(".basecaller.bam"):
                bamFileName = bamFileName.replace(".bam", ".basecaller.bam")
            bamFullPath = os.path.join(reportFullPath, "basecaller_results", bamFileName)

        # sanity check to make sure we do not reference files which don't exist
        if not os.path.exists(bamFullPath):
            logger.warn("Could not find bam file in expected location: " + bamFullPath)

        return bamFullPath

    def dataNonBarcoded(self, start_json):
        """
        Generates a "barcodes" dataset for non-barcoded data
        :param start_json:
        :return:
        """
        data = dict()
        reportFullPath     = self.result.get_report_path()
        # the data structure in this dictionary should be that both the datasets and read_groups for
        # unbarcoded samples should have one and only one instance contained within
        singleDataset   = self.datasetsBaseCaller.get('datasets')[0]
        singleReadGroup = self.datasetsBaseCaller.get('read_groups').itervalues().next()
        unbarcodedEntry = dict()

        # generate the reference genome information
        referenceGenome = singleReadGroup[REFERENCE]
        unbarcodedEntry[REFERENCE] = referenceGenome
        unbarcodedEntry[REFERENCE_FULL_PATH] = os.path.join('/results', 'referenceLibrary', start_json['runinfo']['tmap_version'], referenceGenome, "%s.fasta" % referenceGenome) if start_json is not None and unbarcodedEntry[REFERENCE] else ''
        unbarcodedEntry[ALIGNED] = (REFERENCE in unbarcodedEntry) and bool(unbarcodedEntry[REFERENCE])
        unbarcodedEntry[BAM] = singleDataset['basecaller_bam'] if not unbarcodedEntry[REFERENCE] else "rawlib.bam"
        unbarcodedEntry[FILTERED] = singleReadGroup[FILTERED] if FILTERED in singleReadGroup else False
        unbarcodedEntry[BAM_FULL_PATH] = BarcodeSampleInfo.getFullBamPath(reportFullPath, unbarcodedEntry[REFERENCE], unbarcodedEntry[BAM], unbarcodedEntry[FILTERED])
        unbarcodedEntry[HOT_SPOT_FILE_PATH] = singleDataset[HOT_SPOT_BED] if HOT_SPOT_BED in singleDataset else self.eas.hotSpotRegionBedFile
        unbarcodedEntry[READ_COUNT] = singleReadGroup[READ_COUNT]
        unbarcodedEntry[TARGET_REGION_FILEPATH] = singleDataset[TARGET_REGION_BED] if TARGET_REGION_BED in singleDataset else self.eas.targetRegionBedFile
        unbarcodedEntry[NUCLEOTIDE_TYPE] = ''
        unbarcodedEntry[CONTROL_SEQUENCE_TYPE] = ''
        unbarcodedEntry[SAMPLE] = singleReadGroup[SAMPLE]
        unbarcodedEntry[SAMPLE_ID] = start_json['sampleinfo']['externalId'] if 'sampleInfo' in start_json and 'externalId' in start_json['sampleInfo'] else ''
        unbarcodedEntry[NUCLEOTIDE_TYPE] = ''
        data[NON_BARCODED] = unbarcodedEntry

        # construct the reference genome url which is web accessible
        if start_json and unbarcodedEntry[REFERENCE]:
            runinfo = start_json['runinfo']
            unbarcodedEntry[GENOME_URL] = "/auth/output/" + runinfo['tmap_version'] + "/" + unbarcodedEntry[REFERENCE] + "/" + unbarcodedEntry[REFERENCE] + ".fasta"
        else:
            unbarcodedEntry[GENOME_URL] = ''

        return data

    def dataBarcoded(self, start_json):
        """
        Gets data set for barcoded data
        :param start_json:
        :return:
        """

        def getBarcodeSampleFromEAS(EASbarcodedSamples, barcodeName):
            """
            This helper method will look for the barcode information within the EAS barcodeSamples data structure embedded in dicitonary
            :param EASbarcodedSamples:
            :param barcodeName:
            :return:
            """
            for sample in EASbarcodedSamples.keys():
                barcodeSampleTop = EASbarcodedSamples[sample]
                if barcodeName in barcodeSampleTop['barcodes']:
                    return sample, barcodeSampleTop['barcodeSampleInfo'][barcodeName]
            raise Exception('Cannot find the barcode data from EAS barcodeSamples json structure.')

        data = dict()
        reportFullPath     = self.result.get_report_path()
        # now we are going to handle barcode data and get all of the primary sources of information
        basecallerResults  = self.datasetsBaseCaller
        EASbarcodedSamples = self.barcodedSamples

        for dataset in basecallerResults.get('datasets'):
            barcodeEntry = dict()
            readGroups = dataset['read_groups']
            # currently multiple read_groups on single barcode not supported
            if len(readGroups) != 1:
                logger.warn("Multiple read_groups on single barcode not supported")
                continue

            readGroupId = readGroups[0]

            # many times it seems that the readGroupId is a join between the results runid and barcodeName
            # so they need to break this out and parse the readGroupId
            if '.' in readGroupId:
                runid, barcodeName = readGroupId.split('.', 1)
            else:
                barcodeName = readGroupId

            if NO_MATCH in barcodeName:
                continue

            dnaBarcodeData = dnaBarcode.objects.get(name=self.eas.barcodeKitName, id_str=barcodeName);
            barcodeEntry[BARCODE_ANNOTATION] = dnaBarcodeData.annotation
            barcodeEntry[BARCODE_TYPE] = dnaBarcodeData.type

            # since there should be one and only one read group, we can hard code the first element of the read groups
            singleReadGroup = basecallerResults.get('read_groups')[readGroupId]
            referenceGenome = singleReadGroup[REFERENCE] if REFERENCE in singleReadGroup else self.eas.reference
            barcodeEntry[REFERENCE] = referenceGenome
            barcodeEntry[REFERENCE_FULL_PATH] = os.path.join('/results', 'referenceLibrary', start_json['runinfo']['tmap_version'], referenceGenome, "%s.fasta" % referenceGenome) if start_json is not None and barcodeEntry[REFERENCE] else ''
            barcodeEntry[FILTERED] = singleReadGroup.get(FILTERED, False)

            # if this is a "filtered" barcode, then we will skip including it.
            if barcodeEntry[FILTERED]:
                continue

            barcodeEntry[ALIGNED] = (REFERENCE in barcodeEntry) and bool(barcodeEntry[REFERENCE]) and not barcodeEntry[FILTERED]
            barcodeEntry[BAM] = dataset['file_prefix'] + (".bam" if barcodeEntry[ALIGNED] else ".basecaller.bam")
            barcodeEntry[BAM_FULL_PATH] = BarcodeSampleInfo.getFullBamPath(reportFullPath, barcodeEntry[REFERENCE], barcodeEntry[BAM], barcodeEntry[FILTERED])
            barcodeEntry[HOT_SPOT_FILE_PATH] = dataset[HOT_SPOT_BED] if HOT_SPOT_BED in dataset else self.eas.hotSpotRegionBedFile
            barcodeEntry[READ_COUNT] = singleReadGroup[READ_COUNT]
            barcodeEntry[TARGET_REGION_FILEPATH] = dataset[TARGET_REGION_BED] if TARGET_REGION_BED in dataset else self.eas.targetRegionBedFile
            barcodeEntry[BARCODE_SEQUENCE] = singleReadGroup[BARCODE_SEQUENCE] if BARCODE_SEQUENCE is singleReadGroup else ''
            barcodeEntry[BARCODE_ADAPTER] = singleReadGroup.get(BARCODE_ADAPTER, '')
            barcodeEntry[BARCODE_NAME] = barcodeName
            barcodeEntry[BARCODE_SEQUENCE] = singleReadGroup.get(BARCODE_SEQUENCE, '')
            barcodeEntry[BARCODE_INDEX] = singleReadGroup.get(INDEX, 0)

            # in order to get information out of the EAS.barcodedSamples data structure there needs to be
            # a reverse lookup since the barcode name is a child of the sample id
            barcodeEntry[SAMPLE] = ''
            barcodeEntry[NUCLEOTIDE_TYPE] = ''
            barcodeEntry[CONTROL_SEQUENCE_TYPE] = ''
            barcodeEntry[BARCODE_DESCRIPTION] = ''
            if len(EASbarcodedSamples) > 0:
                # attempt to find the barcode in the EAS BarcodeSample mapping
                try:
                    sample, barcodedSample = getBarcodeSampleFromEAS(EASbarcodedSamples, barcodeName)
                    barcodeEntry[SAMPLE] = sample
                    barcodeEntry[NUCLEOTIDE_TYPE] = barcodedSample['nucleotideType']
                    barcodeEntry[CONTROL_SEQUENCE_TYPE] = barcodedSample['controlSequenceType']
                    barcodeEntry[BARCODE_DESCRIPTION] = barcodedSample[DESCRIPTION]
                except:
                    # intentionally do nothing....
                    pass


            # if a sample has been defined the sample id should be the primary key to look up the sample by
            barcodeEntry[SAMPLE_ID] = start_json['sampleinfo']['externalId'] if  'sampleInfo' in start_json and 'externalId' in start_json['sampleInfo'] else ''

            # construct the reference genome url which is web accessible
            if start_json and barcodeEntry[REFERENCE]:
                runinfo = start_json['runinfo']
                barcodeEntry[GENOME_URL] = "/auth/output/" + runinfo['tmap_version'] + "/" + barcodeEntry[REFERENCE] + "/" + barcodeEntry[REFERENCE] + ".fasta"
            else:
                barcodeEntry[GENOME_URL] = ''

            # assert the entry
            data[barcodeName] = barcodeEntry

        return data

    def data(self, start_json=None):
        """
        This will get a dictionary structure which represents keys for the names of the barcodes and values being a dictionary for each of the data points
        :param start_json:
        :return:
        """

        # we are going to handle unbarcoded data as a special case where as a single item is generated
        if not self.eas.barcodeKitName:
            return self.dataNonBarcoded(start_json)
        else:
            return self.dataBarcoded(start_json)

    @cached_property
    def barcodedSamples(self):
        barcodedSamples = self.eas.barcodedSamples
        if isinstance(barcodedSamples, basestring):

            try:
                barcodedSamples = json.loads(barcodedSamples, encoding=settings.DEFAULT_CHARSET)
            except ValueError as j:
                try:
                    ## What is this? Was barcodedSamples getting python string dumps?
                    barcodedSamples = ast.literal_eval(barcodedSamples)
                except Exception as e:
                    logger.fatal("Unable to parse inputs as json [%s] or python [%s]", j, e)
        try:
            for k,v in barcodedSamples.items():
                if isinstance(v['barcodes'],list):
                    for bc in v['barcodes']:
                        if not isinstance(bc,str):
                            logger.error("INVALID bc - NOT an str - bc=%s" %(bc))
                else:
                    logger.error("INVALID v[barcodes] - NOT a list!!! v[barcodes]=%s" %(v['barcodes']))
        except:
            logger.exception("Invalid barcodedSampleInfo value")
        return barcodedSamples

    @cached_property
    def datasetsBaseCaller(self):
        datasetsBaseCallerFile = os.path.join(self.result.get_report_path(), "basecaller_results", "datasets_basecaller.json")
        with open(datasetsBaseCallerFile) as f:
            datasetsBaseCaller = json.load(f, encoding=settings.DEFAULT_CHARSET)

        # File is tagged with a version number (yay!). Best check it.
        ver = datasetsBaseCaller.get('meta',{}).get('format_version', "0")
        if ver != "1.0":
            logger.warn("Basecaller JSON file syntax has unrecognized version: %s", ver)
        return datasetsBaseCaller




