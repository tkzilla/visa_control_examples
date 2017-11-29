% VISA Control: RSA AvT Transfer
% Author: Morgan Allison
% Updated: 11/17
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
fprintf(inst, 'system:preset')
fprintf(inst, '*cls')
fprintf(inst, 'abort')


%% #################INITIALIZE VARIABLES#################
% Configure acquisition parameters.
cf = 2.4453e9;
span = 40e6;
refLevel = 0;
timeScale = 100e-6;
timeOffset = 0;
trigLevel = -10;


%% #################CONFIGURE INSTRUMENT#################
% Stop acquisitions while setting up instrument.
fprintf(inst, 'abort');

% Open spectrum, time overview, and amplitude vs time displays.
fprintf(inst, 'display:general:measview:new spectrum');
fprintf(inst, 'display:general:measview:new toverview');
fprintf(inst, 'display:general:measview:new avtime');

% Configure amplitude vs time measurement.
fprintf(inst, 'spectrum:frequency:center %d', cf);
fprintf(inst, 'spectrum:frequency:span %d', span);
fprintf(inst, 'input:rlevel %d', refLevel);
fprintf(inst, 'sense:avtime:span %d', span);
fprintf(inst, 'sense:analysis:length %d', timeScale);
fprintf(inst, 'sense:analysis:start %d', timeOffset);

% Configure power level trigger.
fprintf(inst, 'trigger:event:input:type power');
fprintf(inst, 'trigger:event:input:level %d', trigLevel);
fprintf(inst, 'initiate:continuous off');
fprintf(inst, 'trigger:status on');


%% #################ACQUIRE/PROCESS DATA#################
% Start acquisition.
fprintf(inst, 'initiate:immediate');
query(inst, '*opc?');

% Get raw amplitude vs time data from RSA.
fprintf(inst, 'fetch:avtime:first?');
avt = binblockread(inst, 'float');

acqStart = str2num(query(inst, 'display:avtime:x:scale:offset?'));
acqEnd = str2num(query(inst, 'display:avtime:x:scale:full?'));
time = linspace(acqStart, acqEnd, length(avt));


%% #################PLOTS#################
figure(1);
whitebg(1,'k');
plot(time, avt, 'y');
title('Amplitude vs Time');
ylabel('Amplitude (dBm)');
xlabel('Time (s)');
xlim([acqStart, acqEnd]);


%% Close inst
fclose(inst);
delete(inst);
clear inst;
