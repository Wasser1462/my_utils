#include <iostream>
#include <fstream>
#include <cstring>
#include <cstdint>

struct WavHeader {
    char riff[4] = {'R','I','F','F'};     
    uint32_t fileSize;                   
    char wave[4] = {'W','A','V','E'};       
    char fmt[4] = {'f','m','t',' '};     
    uint32_t fmtSize = 16;             
    uint16_t audioFormat = 1;           
    uint16_t numChannels = 1;  // 默认单声道           
    uint32_t sampleRate;               
    uint32_t byteRate;                  
    uint16_t blockAlign;                  
    uint16_t bitsPerSample = 16;        
    char data[4] = {'d','a','t','a'};      
    uint32_t dataSize;                  
};

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input.pcm> [output.wav] [sample_rate]\n";
        std::cerr << "Example: " << argv[0] << " input.pcm output.wav 16000\n";
        std::cerr << "Defaults: output.wav, sample_rate=16000, channels=2\n";
        return 1;
    }

    const char* inputFile = argv[1];
    const char* outputFile = (argc >= 3) ? argv[2] : "output.wav";
    uint32_t sampleRate = (argc >= 4) ? std::stoi(argv[3]) : 16000;  

    std::ifstream pcm(inputFile, std::ios::binary | std::ios::ate);
    if (!pcm) {
        std::cerr << "Error opening PCM file: " << inputFile << std::endl;
        return 1;
    }

    uint32_t pcmSize = pcm.tellg();
    pcm.seekg(0, std::ios::beg);

    WavHeader header;
    header.sampleRate = sampleRate;             
    header.blockAlign = header.numChannels * header.bitsPerSample / 8;
    header.byteRate = sampleRate * header.blockAlign; 
    header.dataSize = pcmSize;                   
    header.fileSize = 36 + header.dataSize;     

    std::ofstream wav(outputFile, std::ios::binary);
    if (!wav) {
        std::cerr << "Error creating WAV file: " << outputFile << std::endl;
        return 1;
    }

    wav.write(reinterpret_cast<char*>(&header), sizeof(WavHeader));
    
    char* buffer = new char[pcmSize];
    pcm.read(buffer, pcmSize);
    wav.write(buffer, pcmSize);
    delete[] buffer;

    std::cout << "Converted " << pcmSize << " bytes PCM to WAV:\n"
              << "Channels: " << header.numChannels << " (stereo)\n"
              << "Sample Rate: " << sampleRate << " Hz\n"
              << "Output: " << outputFile << std::endl;
    
    pcm.close();
    wav.close();
    return 0;
}