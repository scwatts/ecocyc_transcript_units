#!/usr/bin/env python3

# This script takes a file of EcoCyc gene names and returns the transcript gene
# units (with assocaited promoter) for each gene

# We're going to have to do this in two parts:
#   1. Convert gene names to accessions via API search
#   2. Make HTTP requests to API to grab common-name for transcript units and promoter
#       2a. If common-name for promoter does not exist, make another request
#           for the promoter XML object and extract from there


import argparse
import os
import xml.etree.ElementTree as et


import requests


# Constants
GENE_SEARCH_URL = 'http://websvc.biocyc.org/xmlquery?[g:g<-ecoli^^all-genes,g^common-name="%s"]'
TS_UNIT_URL = 'http://ecocyc.org/apixml?fn=transcription-units-of-gene&id=%s'
TS_PROMOTOR_URL = 'http://ecocyc.org/apixml?fn=transcription-unit-promoter&id=%s'


def get_arguments():
    # Set arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--genes', required=True, help=('File containing'
        ' genes names'))

    # Check arguments
    args = parser.parse_args()
    if not os.path.exists(args.genes):
        parser.error('Input genes file %s does not exist' % args.genes)

    return args


def main():
    # Get and parse command line arguments
    args = get_arguments()

    # Read in gene names
    with open(args.genes) as f:
        genes = [l.rstrip() for l in f]

    # For each gene, do the thing
    for gene in genes:
        ####
        # Part 1: Get accession for gene
        ####
        # Make request for query (extact match for gene name, case sensitive)
        gene_search_response = requests.get(GENE_SEARCH_URL % gene)

        # Convert parse XML structure and grab the Gene tag
        gene_search_xml = et.fromstring(gene_search_response.text)
        gene_tag = gene_search_xml.find('Gene')

        if not gene_tag:
            print(gene, 'no_gene_found_in_ecoli_db')
            continue

        gene_accession = gene_tag.get('ID')


        ####
        # Part 2: Get the promoter name and transcript gene unit
        ####
        # Make initial request for transcript unit and parse XML
        ts_unit_response = requests.get(TS_UNIT_URL % gene_accession)
        ts_unit_xml = et.fromstring(ts_unit_response.text)

        # Extract desired parts from XML
        for ts in ts_unit_xml.findall('Transcription-Unit'):


            unit_genes_tag = ts.find('common-name')
            if not unit_genes_tag:
                unit_genes = gene
            else:
                unit_genes = unit_genes_tag.text


            ts_accession = ts.get('ID')


            # Get transcript unit promoter xml
            ts_promoters_response = requests.get(TS_PROMOTOR_URL % ts_accession)
            ts_promoter_xml = et.fromstring(ts_promoters_response.text)


            ts_promoters = ts_promoter_xml.findall('Promoter/common-name')

            if not ts_promoters:
                print(gene, 'no_promoter_with_evidence')
                continue

            for ts_promoter in ts_promoters:
                promoter_name = ts_promoter.text
                print(gene, promoter_name, unit_genes, sep='\t', flush=True)


if __name__ == '__main__':
    main()
