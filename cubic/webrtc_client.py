# -*- coding: utf-8 -*-
#
# Copyright(2021) Cobalt Speech and Language Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http: // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import asyncio
import requests
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

def channel_log(channel, separator, message):
    print("channel(%s) %s %s" % (channel.label, separator, message))

def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)

def create_local_tracks(play_from):
    player = MediaPlayer(play_from)
    return player.audio
    
def sendOfferCubicsvr(sdp)->RTCSessionDescription:
    # host of cubicsvr
    url = "http://localhost:8000/webrtc"
    # cubic modelID
    modelId = "en_US-16-FF"
    action_item = requests.post(url, json={
            "Config": {
                "ModelID":                  modelId,
                "EnableWordTimeOffsets":    True,
                "EnableWordConfidence":     True, 
                "EnableRawTranscript":      False,
                "EnableConfusionNetwork":   False
            },
            "Description": {
                "type": "offer",
                "sdp":  sdp
            }
    })

    json = action_item.json()
    return RTCSessionDescription(json['sdp'], json['type'])

async def start():
    while True:
        await asyncio.sleep(1)

# Web browser and Pion (golang WebRTC library) expect similar Pion 'ice-ufrag' and 'ice-pwd' for each stream.
# Python aiortc library generates different values for each data channel. 
# We fix it in the 'sdp' by setting the same 'ice-ufrag' and 'ice-pwd' values.
#
#   Link: https://github.com/aiortc/aioice/blob/26abbb23e485aed9a338208f53b81727c3ca6206/src/aioice/ice.py#L290
#

def sdpPionFix(sdp):
    ufrag = None
    icePwd = None
    newOfferSdp = "" 
    for item in sdp.split('\n'): 
        if "a=ice-ufrag" in item:
            if ufrag is None:
                ufrag=item
            newOfferSdp+=ufrag+"\n"
        else:
            if "a=ice-pwd:" in item:
                if icePwd is None:
                    icePwd=item
                newOfferSdp+=icePwd+"\n"
            else:
                newOfferSdp+=item+"\n"
    return newOfferSdp

async def createOffer(pc)->RTCSessionDescription:
    offer = await pc.createOffer()
    localSd = RTCSessionDescription(sdp=sdpPionFix(offer.sdp), type=offer.type)
    await pc.setLocalDescription(localSd)
    sdp = sdpPionFix(pc.localDescription.sdp)
    return RTCSessionDescription(sdp,offer.type)

async def main():
        pc = RTCPeerConnection()
        
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
                print("Connection state is %s" % pc.connectionState)
                if pc.connectionState == "failed":
                        await pc.close()
       
        @pc.on('error')
        def on_error(message):
            print("rtc peer connection error: "+str(message))

        @pc.on("datachannel")
        def on_datachannel(channel):
                channel_log(channel, "-", "created by remote party")

                @channel.on("message")
                def on_message(message):
                    channel_log(channel, "<", message)
                    with open('webrtc_result.txt', 'a') as the_file:
                        the_file.write(str(message, 'utf-8')+'\n')
        # add audio streams
        audio = create_local_tracks("samples/travel1-left.wav")
        pc.addTrack(audio)
        audio1 = create_local_tracks("samples/travel1-right.wav")
        pc.addTrack(audio1)
        channel = pc.createDataChannel("output_data_channel")

        @channel.on("open")
        def on_open():
            print("output_data_channel channel is opened")

        @channel.on("message")
        def on_message(message):
            channel_log(channel, "<", message)
            
        offer = await createOffer(pc)
        answerDescription = sendOfferCubicsvr(offer.sdp)
        await pc.setRemoteDescription(answerDescription)
        await start()
        

   
asyncio.get_event_loop().run_until_complete(main())
