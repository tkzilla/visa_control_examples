% VISA Control: RSA Digital Demod
% Author: Morgan Allison
% Updated 11/17
% This program transfers the Amplitude vs Time trace from the RSA to the 
% computer and plots the results. 
% Windows 7 64-bit, TekVISA 4.0.4
% Matlab r2017a with ICT
% Download SignalVu-PC programmer manual:
% https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
% Download RSA5100B programmer manual:
% http://www.tek.com/spectrum-analyzer/inst5000-manual-7
% Tested on RSA306B, RSA507A, DPO77002SX


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

if contains(instID, 'MSO') || contains(instID, 'DPO')
    % IMPORTANT: make sure SignalVu is already running if you're using a scope.
    % The application:activate command gives focus to SignalVu.
    % *OPC? does not respond to application:activate, so there's no good 
    % way to synchronize this command
    sampleRate = 50e9;

    disp('Activating SignalVu');
    fprintf(inst, 'application:activate "SignalVu Vector Signal Analysis Software"');
    fprintf(inst, 'sense:signalvu:acquisition:control:sample:rate off');
    fprintf(inst, 'sense:signalvu:acquisition:digitizer:sample:rate %d', sampleRate);
end

% Preset, clear buffer, and stop acquisition.
fprintf(inst, 'system:preset');
fprintf(inst, '*cls');
fprintf(inst, 'abort');


%% #################CONFIGURE INSTRUMENT#################
freq = 1e9;
span = 40e6;
refLevel = 0;

% Set up spectrum acquisition parameters.
fprintf(inst, 'spectrum:frequency:center %d', freq);
fprintf(inst, 'spectrum:frequency:span %d', span);
fprintf(inst, 'input:rlevel %d', refLevel);

% Open new displays.
fprintf(inst, 'display:ddemod:measview:new conste'); % constellation
fprintf(inst, 'display:ddemod:measview:new stable'); % symbol table
fprintf(inst, 'display:ddemod:measview:new evm'); % EVM vs Time

% Turn off trigger and disable continuous capture (single shot mode).
fprintf(inst, 'trigger:status off');
fprintf(inst, 'initiate:continuous off');

% Configure digital demod (QPSK, 3.84 MSym/s, RRC/RC filters, alpha 0.22)
symRate = 3.84e6;
alpha = 0.22;

fprintf(inst, 'sense:ddemod:modulation:type qpsk');
fprintf(inst, 'sense:ddemod:srate %d', symRate);
fprintf(inst, 'sense:ddemod:filter:measurement rrcosine');
fprintf(inst, 'sense:ddemod:filter:reference rcosine');
fprintf(inst, 'sense:ddemod:filter:alpha %d', alpha);
fprintf(inst, 'sense:ddemod:symbol:points one');
% fprintf(inst, 'sense:ddemod:analysis:length 20000');
% fprintf(query(inst, 'sense:acquisition:samples?'));


%% #################ACQUIRE DATA#################
% start acquisition
fprintf(inst, 'initiate:immediate');
inst.timeout = 30;
query(inst, '*opc?');

% query results from the constellation display (details in programmer manual)
results = str2num(query(inst, 'fetch:conste:results?'));

% Print out the constellation results.
fprintf('EVM (RMS): %2.3f%%, EVM (peak): %2.3f%%, Symbol: %4.0f\n', results);

% Get EVM vs time data
fprintf(inst, 'fetch:evm:trace?');
evmVsTime = binblockread(inst, 'float');

plot(evmVsTime)
title('EVM vs Symbol #')
xlabel('Symbol')
ylabel('EVM (%)')

%% Close instrument
fclose(inst);
delete(inst);
clear inst;
