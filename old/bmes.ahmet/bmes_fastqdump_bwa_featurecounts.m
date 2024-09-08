function [genecountfile,genetable]=bmes_fastqdump_bwa_featurecounts(srrid,genomefile,genomeannotfile,genefield,genecountfile,cleanup)
% Run fastqdump to download a SRR fastq file, then run bwa against a
% genome to produce a sam file, then run featurecounts to produce
% genecounts.
% genomefile and gtffile can be URLs or local files. We'll download
% here if URL is given.
% See also: bmes_fastqdump(), bmes_bwa(), and bmes_featurecounts() for additional information.
% Use cleanup=true to remove unneeded fastq and sam files (which are no
% longer needed once the genecountfile is produced.
%{
Example Usage:
==============
>> srrid = 'SRR8482616';
>> genomefile = 'https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_genomic.fna.gz';
>> genomeannotfile = 'https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_genomic.gff.gz';
>> [genecountfile,genetable] = bmes_fastqdump_bwa_featurecounts( srrid,genomefile, genomeannotfile )
%}
%by Ahmet Sacan

if ~exist('srrid','var')
	warning(sprintf('No inputs given.\n   Using example files for demonstration purposes only.\n   You must provide your own inputs for the problem you are investivating.'));
	% This is a human (Alzheimer's disease) experiment example:
	srrid = 'SRR8482616';
	%genome and annotation urls are obtained from: https://www.ncbi.nlm.nih.gov/genome/guide/human/
	genomefile = 'https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_genomic.fna.gz';
	genomeannotfile = 'https://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_genomic.gff.gz';
	genefield='gene';
end


if ~exist('genefield','var'); genefield=''; end
if ~exist('genecountfile','var'); genecountfile=''; end

if isempty(genecountfile)
	fastqfile=bmes_fastqdump(srrid,true);
	% these naming rules must match what is used in bmes_bwa() and
	% bmes_featurecounts()
	samfile=[fastqfile '.sam'];
	genecountfile=[samfile '.' genefield '.genecount'];
end


if ~bmes.isfileandnotempty(genecountfile)
	fastqfile=bmes_fastqdump(srrid);
	samfile=bmes_bwa(fastqfile,genomefile);
end

if nargout>1
	[genecountfile,genetable]=bmes_featurecounts(samfile,genomeannotfile,genefield,genecountfile);
else
	[genecountfile]=bmes_featurecounts(samfile,genomeannotfile,genefield,genecountfile);
end


if ~exist('cleanup','var'); cleanup=false; end
if cleanup
	if bmes.isfile(fastqfile); delete(fastqfile); end
	if bmes.isfile(fastqfile); delete(samfile); end
end
