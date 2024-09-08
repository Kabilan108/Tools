function [sams]=sam_keepbestofmultimap(sams,varargin)
% bwa returns both forward and reverse maps for some reads or it may
% provide alternative "supplementary alignments". Here we check for such
% cases and keep the better (cityblockdist) alignment among the two.
% Copyright (C) 2019 by Ahmet Sacan

if false&&any(exist('sam_enrich')==[2 5 6])
	sams=sam_enrich(sams,'enrichfields','revcomp,cityblockdist',varargin{:});
else
	assert(strcmp(varargin{1},'genomefile'));
	g=fastaread(varargin{2});
	gseq=g.Sequence;
	for si=1:numel(sams)
		sam=sams(si);
		if bitand(uint16(sam.Flag), uint16(4)); sam.cityblockdist=inf;
		else
			gsubseq=gseq(sam.Position:min(end,sam.Position+numel(sam.Sequence)-1));
			%TODO: this is not really a correct implementation. The sequences are
			%not pre-aligned. You need to either use the CIGAR string to
			%reconstruct the alignment; or use nwalign to re-align them.
			sams(si).cityblockdist=nnz(gsubseq~=sam.Sequence(1:numel(gsubseq)))+numel(sam.Sequence)-numel(gsubseq);
		end
	end
end
Iremove = false(size(sams));
i=1;
while i<numel(sams)
	%using 2048 is not reliable. using queryname identity is better.
	%assert(~bitand(uint16(sams(i).Flag),uint16(2048))); %first of the block should not be a supplementaryalignment.
	ibegin=i;
	%while i+1<numel(sams) && bitand(uint16(sams(i+1).Flag),uint16(2048))
	while i+1<=numel(sams) && strcmp(sams(i).QueryName,sams(i+1).QueryName)
		%assert(strcmp(sams(i).QueryName,sams(i+1).QueryName));
		i=i+1;
	end
	if i~=ibegin
		[~,Ibest]=min([sams(ibegin:i).cityblockdist]);
		Iremove(ibegin:i)=true;
		Iremove(ibegin+Ibest-1)=false;
	end

	i=i+1;
end
if any(Iremove); sams(Iremove)=[]; end

assert(numel(unique({sams.QueryName}))==numel(sams));
