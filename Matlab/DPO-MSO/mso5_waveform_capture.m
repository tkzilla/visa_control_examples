% VISA Control: Basic Waveform Capture
% Author: Morgan Allison
% Updated: 03/18
% This program acquires the Probe Compensation signal 
% on the scope and transfers it to the computer.
% Windows 10 64-bit, TekVISA 4.0.4
% Tested on MSO58

%% #################SEARCH/CONNECT#################
mso = visa('tek', 'TCPIP::192.168.1.14::INSTR');
set(mso, 'ByteOrder', 'bigEndian');
mso.InputBufferSize = 125000;
mso.OutputBufferSize = 125000;
mso.Timeout = 10;
fopen(mso);

msoID = query(mso, '*idn?');
fprintf('Connected to %s\n', msoID);


%% #################CONFIGURE msoRUMENT#################
hScale = 1e-6;
sampleRate = 3.125e9;
vScale = 400e-3;
vPos = -2.5;
trigLevel = 1.25;

fprintf(mso, '*rst');
query(mso, '*opc?');

fprintf(mso, 'acquire:stopafter sequence');
fprintf(mso, 'horizontal:scale %d', hScale);
fprintf(mso, 'horizontal:samplerate:analyzemode:minimum:value %d', sampleRate);
fprintf(mso, 'horizontal:samplerate %d', sampleRate);
fprintf(mso, 'ch1:position %d', vPos);
fprintf(mso, 'ch1:scale %d', vScale);

fprintf(mso, 'trigger:a:type edge');
fprintf(mso, 'trigger:a:level:ch1 %d', trigLevel);
rl = query(mso, 'horizontal:mode:recordlength?');

fprintf(mso, 'data:source ch1');
fprintf(mso, 'wfmoutpre:byt_nr 2');
fprintf(mso, 'data:stop %s', rl);

%% #################ACQUIRE DATA#################
fprintf(mso, 'acquire:state on');
disp(query(mso, '*opc?'));

fprintf(mso, 'curve?');
data = binblockread(mso, 'int16');
if fread(mso, 1) ~= 10
    disp('Incorrect termination.')
else
    % Apply scaling factors
    yoffset = str2double(query(mso,'wfmoutpre:yoff?'));
    ymult = str2double(query(mso,'wfmoutpre:ymult?'));
    yzero = str2double(query(mso,'wfmoutpre:yzero?'));
    scaledData = (data-yoffset).*ymult+yzero;

    % Create robust time scale
    ptOffset = str2double(query(mso, 'wfmoutpre:pt_off?'));
    dTime = str2double(query(mso, 'horizontal:delay:time?'));
    numPoints = str2double(query(mso,'wfmoutpre:nr_pt?;'));
    xIncr = str2double(query(mso,'wfmoutpre:xincr?;'));
    start = -dTime + (xIncr*-ptOffset);
    stop = -dTime + xIncr*(numPoints-ptOffset);
    scaledTime = linspace(start, stop, numPoints);
    
    plot(scaledTime, scaledData);
    title('Scope Waveform');
    xlabel('Time (s)');
    ylabel('Voltage (V)');
end
    
query(mso, '*esr?');
disp(query(mso, 'allev?'));

%% Close msorument
fclose(mso);
delete(mso);
clear mso;
