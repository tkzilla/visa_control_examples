% VISA Control: RSA DPX Trace Selector
% Author: Morgan Allison
% Updated: 11/17
% This program opens a split DPX display and lets user select the available 
% traces. Trace numbers in VISA commands are interpreted in comments below.
% Windows 7 64-bit, TekVISA 4.0.4
% Matlab r2017a with ICT
% Download SignalVu-PC programmer manual:
% https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
% Download RSA5100B programmer manual:
% http://www.tek.com/spectrum-analyzer/inst5000-manual-7
% Tested on RSA306B, RSA507A


%% #################SEARCH/CONNECT#################
visaBrand = 'tek';
% instAddress = 'TCPIP::192.168.1.10::INSTR';
instAddress = 'GPIB8::1::INSTR';
buf = 50000;
inst = visa(visaBrand, instAddress);
set(inst, 'InputBuffer', buf);
set(inst, 'OutputBuffer', buf);
fopen(inst);
inst.timeout = 15;

instID = query(inst,'*idn?');
fprintf('Connected to %s\n',instID);

% Preset, clear buffer, and stop acquisition.
fprintf(inst, 'system:preset');
fprintf(inst, '*cls');
fprintf(inst, 'abort');


%% #################INITIALIZE VARIABLES#################
% Configure acquisition parameters.
cf = 2.4453e9;
span = 40e6;

%% #################CONFIGURE INSTRUMENT#################
% Configure DPX measurement.
fprintf(inst, 'display:general:measview:new DPX');
fprintf(inst, 'sense:dpx:plot split');
fprintf(inst, 'spectrum:frequency:center %d', cf);
fprintf(inst, 'spectrum:frequency:span %d', span);

%% #################ACQUIRE/PROCESS DATA#################
fprintf(inst, 'initiate:immediate');
query(inst, '*opc?');
fprintf(inst, 'trace1:dpx 1');  % Trace 1
fprintf(inst, 'trace2:dpx 1');  % Trace 2
fprintf(inst, 'trace3:dpx 1');  % Trace 3
fprintf(inst, 'trace4:dpx 0');  % Math
fprintf(inst, 'trace5:dpx 1');  % Bitmap
fprintf(inst, 'trace6:dpx 1');  % DPXogram
fprintf(inst, 'trace7:dpx 1');  % DPXogram Line


%% Close inst
fclose(inst);
delete(inst);
clear inst;
