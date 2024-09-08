function [sams]=sam_removesupplementary(sams)
% BWA may result in multiple alignments of a short read. Here, we remove
% all alignments marked as supplementary. WARNING: We are not checking if
% theres is non-supplementary alignment for each read or if it is the best
% one.
% Copyright (C) 2019 by Ahmet Sacan

Iremove=false(size(sams));
for si=1:numel(sams)
	if bitand(uint16(sams(si).Flag), uint16(2048))
		Iremove(si)=true;
	end
end
if any(Iremove); sams(Iremove)=[]; end
