#!/usr/bin/env python3
"""V9: user-approved Chrome playback capture feasibility test.

This is NOT a Yoda audio bridge. With explicit Android MediaProjection consent,
it measures only amplitude of Chrome playback; no speech content is saved,
transmitted, recorded to a file, or sent to Szuhay.
"""
from pathlib import Path
base=Path("android-one-icon")
app=base/"app"
java=app/"src/main/java/hu/alya/yoda/MainActivity.java"
src=java.read_text(encoding="utf-8")
def replace_once(old,new,label):
    global src
    count=src.count(old)
    if count!=1: raise RuntimeError(f"{label}: expected 1 anchor, got {count}")
    src=src.replace(old,new)
replace_once("import android.content.Intent;\n",
"""import android.content.Intent;
import android.media.projection.MediaProjectionManager;
""","projection imports")
replace_once("    private static final int MIC_REQUEST=42;",
"""    private static final int MIC_REQUEST=42;
    private static final int CAPTURE_REQUEST=90;
    private static final int CAPTURE_MIC_PERMISSION=91;""","request codes")
replace_once('        if ("openChromeSession".equals(type)) {',
"""        if ("audioProbeStatus".equals(type)) {
            String status=getSharedPreferences("alya_audio_probe",MODE_PRIVATE)
                .getString("status","A Chrome-hang próbája még nem futott.");
            return GeckoResult.fromValue(reply("probe",status));
        }
        if ("startChromeAudioProbe".equals(type)) {
            runOnUiThread(()->startChromeAudioProbe());
            return GeckoResult.fromValue(reply("requested",true));
        }
        if ("openChromeSession".equals(type)) {""","native message handling")
replace_once('    private void openChromeSessionProbe() {',
"""    private void startChromeAudioProbe() {
        // This requires a separate, visible Android consent; NEVER try
        // to obtain recording privileges without the user's approval.
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},CAPTURE_MIC_PERMISSION);
            return;
        }
        try{
            speech.stop();
            MediaProjectionManager manager=(MediaProjectionManager)getSystemService(MEDIA_PROJECTION_SERVICE);
            if(manager==null) throw new IllegalStateException("Android MediaProjection nem elérhető");
            startActivityForResult(manager.createScreenCaptureIntent(),CAPTURE_REQUEST);
        } catch(Exception e) {
            getSharedPreferences("alya_audio_probe",MODE_PRIVATE).edit()
                .putString("status","A rendszer nem engedte a hangpróba indítását: "+e.getClass().getSimpleName()).apply();
        }
    }

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=CAPTURE_REQUEST)return;
        if(resultCode!=RESULT_OK || data==null){
            getSharedPreferences("alya_audio_probe",MODE_PRIVATE).edit()
                .putString("status","A Chrome-hang tesztelése megszakadt: nem volt rendszerengedély.").apply();
            return;
        }
        getSharedPreferences("alya_audio_probe",MODE_PRIVATE).edit()
            .putString("status","A Chrome-hang tesztelése folyamatban. 90 másodpercig csak a hangszintet mérjük.").apply();
        Intent service=new Intent(this,ChromeAudioProbeService.class);
        service.putExtra("result_code",resultCode);
        service.putExtra("projection_data",data);
        startForegroundService(service);
        // Only open the actual Chrome after Android grants explicit consent.
        // The user must then manually start a genuine ChatGPT Read Aloud answer.
        openChromeSessionProbe();
    }

    private void openChromeSessionProbe() {""","capture consent flow")
replace_once('        if(requestCode==MIC_REQUEST && startRecognitionAfterPermission) {',
"""        if(requestCode==CAPTURE_MIC_PERMISSION){
            if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)
                startChromeAudioProbe();
            else getSharedPreferences("alya_audio_probe",MODE_PRIVATE).edit()
                .putString("status","Mikrofonengedély nélkül a Chrome-hang tesztelése nem indítható.").apply();
            return;
        }
        if(requestCode==MIC_REQUEST && startRecognitionAfterPermission) {""","mic permission flow")
java.write_text(src,encoding="utf-8")

service=app/"src/main/java/hu/alya/yoda/ChromeAudioProbeService.java"
service.write_text(r'''package hu.alya.yoda;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.ServiceInfo;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.AudioPlaybackCaptureConfiguration;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;

import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/** Local-only Chrome playback level test. NEVER stores or transmits PCM. */
public final class ChromeAudioProbeService extends Service {
    private static final String CHANNEL="alya_audio_probe";
    private static final String STOP="hu.alya.yoda.STOP_AUDIO_PROBE";
    private final AtomicBoolean running=new AtomicBoolean(false);
    private AudioRecord recorder;
    private MediaProjection projection;
    private Thread worker;

    @Override public IBinder onBind(Intent intent){return null;}
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent==null) {stopSelf();return START_NOT_STICKY;}
        if(STOP.equals(intent.getAction())){
            stopProbe("A hangpróbát a felhasználó leállította.");
            return START_NOT_STICKY;
        }
        if(!running.compareAndSet(false,true))return START_NOT_STICKY;
        try{
            NotificationManager nm=getSystemService(NotificationManager.class);
            nm.createNotificationChannel(new NotificationChannel(CHANNEL,
                "Alya–Yoda helyi hangpróba",NotificationManager.IMPORTANCE_LOW));
            Intent stopIntent=new Intent(this,ChromeAudioProbeService.class).setAction(STOP);
            PendingIntent pending=PendingIntent.getService(this,0,stopIntent,
                PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
            Notification notice=new Notification.Builder(this,CHANNEL)
                .setSmallIcon(android.R.drawable.ic_media_play)
                .setContentTitle("Alya–Yoda: Chrome-hang ellenőrzése")
                .setContentText("Csak hangerőt mérünk; hangfelvételt nem tárolunk.")
                .addAction(android.R.drawable.ic_media_pause,"Próba leállítása",pending)
                .setOngoing(true).build();
            startForeground(65,notice,ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
            int resultCode=intent.getIntExtra("result_code",0);
            @SuppressWarnings("deprecation")
            Intent data=intent.getParcelableExtra("projection_data");
            MediaProjectionManager manager=(MediaProjectionManager)getSystemService(MEDIA_PROJECTION_SERVICE);
            if(manager==null||data==null)throw new IllegalStateException("MediaProjection hiányzik");
            projection=manager.getMediaProjection(resultCode,data);
            if(projection==null)throw new IllegalStateException("MediaProjection engedély hiányzik");
            projection.registerCallback(new MediaProjection.Callback(){
                @Override public void onStop(){
                    stopProbe("Az Android visszavonta a hangrögzítési engedélyt.");
                }
            },new Handler(Looper.getMainLooper()));
            // Capture only *this* Chrome installation, not the room mic or other apps.
            ApplicationInfo chrome=getPackageManager().getApplicationInfo("com.android.chrome",0);
            AudioPlaybackCaptureConfiguration filter=new AudioPlaybackCaptureConfiguration.Builder(projection)
                .addMatchingUid(chrome.uid)
                .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
                .addMatchingUsage(AudioAttributes.USAGE_GAME)
                .addMatchingUsage(AudioAttributes.USAGE_UNKNOWN)
                .build();
            AudioFormat format=new AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(48000)
                .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
                .build();
            recorder=new AudioRecord.Builder().setAudioFormat(format)
                .setBufferSizeInBytes(32768).setAudioPlaybackCaptureConfig(filter).build();
            if(recorder.getState()!=AudioRecord.STATE_INITIALIZED)
                throw new IllegalStateException("AudioRecord nem indítható");
            recorder.startRecording();
            worker=new Thread(this::measure,"alya-chrome-rms-only");
            worker.start();
        }catch(Exception ex){
            Log.w("AlyaAudioProbe","Probe startup",ex);
            stopProbe("A Chrome-hang tesztelése nem indult: "+ex.getClass().getSimpleName());
        }
        return START_NOT_STICKY;
    }
    private void measure(){
        long deadline=SystemClock.elapsedRealtime()+90000L;
        long blocks=0,nonzero=0,peak=0;
        short[] buffer=new short[4096];
        try{
            while(running.get()&&SystemClock.elapsedRealtime()<deadline){
                AudioRecord r=recorder;
                if(r==null)break;
                int n=r.read(buffer,0,buffer.length,AudioRecord.READ_BLOCKING);
                if(n<0)throw new IllegalStateException("AudioRecord read "+n);
                if(n==0)continue;
                blocks++;
                long localPeak=0;
                for(int i=0;i<n;i++){
                    long amplitude=Math.abs((int)buffer[i]);
                    if(amplitude>localPeak)localPeak=amplitude;
                }
                if(localPeak>100)nonzero++;
                if(localPeak>peak)peak=localPeak;
            }
            final String message="Chrome-hangpróba kész: "+nonzero+"/"+blocks+
                " hangot tartalmazó blokk; csúcs "+peak+
                ". Ha a próba alatt a ChatGPT felolvasása hallatszott, a 0 érték tiltott vagy nem elérhető hangátvételt jelezhet.";
            stopProbe(message);
        }catch(Exception ex){
            Log.w("AlyaAudioProbe","Playback sample probe",ex);
            stopProbe("A Chrome-hang tesztelése közben hiba: "+ex.getClass().getSimpleName());
        }
    }
    private void stopProbe(String message){
        if(!running.getAndSet(false))return;
        getSharedPreferences("alya_audio_probe",MODE_PRIVATE).edit()
            .putString("status",message).apply();
        AudioRecord r=recorder;recorder=null;
        if(r!=null){
            try{r.stop();}catch(Exception ignored){}
            try{r.release();}catch(Exception ignored){}
        }
        MediaProjection p=projection;projection=null;
        if(p!=null)try{p.stop();}catch(Exception ignored){}
        stopForeground(STOP_FOREGROUND_REMOVE);
        stopSelf();
    }
    @Override public void onDestroy(){
        if(running.get())stopProbe("A hangpróba leállt.");
        super.onDestroy();
    }
}
''',encoding="utf-8")

manifest=app/"src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
old='  <uses-permission android:name="android.permission.RECORD_AUDIO"/>'
assert m.count(old)==1
m=m.replace(old,old+'''
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
  <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION"/>''')
old='  <queries>'
assert m.count(old)==1
m=m.replace(old,'''  <queries>
    <package android:name="com.android.chrome"/>''')
old='    <activity android:name=".MainActivity"'
assert m.count(old)==1
m=m.replace(old,'''    <service android:name=".ChromeAudioProbeService"
      android:exported="false" android:foregroundServiceType="mediaProjection"/>
    <activity android:name=".MainActivity"''')
manifest.write_text(m,encoding="utf-8")

bridge=app/"src/main/assets/yodabridge/bridge.js"
s=bridge.read_text(encoding="utf-8")
old="'openChromeSession'];"
assert s.count(old)==1
s=s.replace(old,"'openChromeSession','startChromeAudioProbe','audioProbeStatus'];")
bridge.write_text(s,encoding="utf-8")

page=app/"src/main/assets/yodabridge/page.js"
s=page.read_text(encoding="utf-8")
old='    root.append(heading,description,btn,note,setup,chromeProbe);'
assert s.count(old)==1
s=s.replace(old,'''    const audioProbe=document.createElement('button');
    audioProbe.textContent='Chrome-hang átvételének tesztje (Android engedéllyel)';
    audioProbe.style.cssText='min-height:48px;background:transparent;color:#d2e7c0;'
      +'border:1px solid #70836d;border-radius:9px;padding:10px 15px;font:15px system-ui';
    audioProbe.addEventListener('click',()=>{
      label('A rendszer hangrögzítési engedélyt kér. A teszt csak hangerőt mér, és nem küld hangot sehova.');
      nativeCommand('startChromeAudioProbe');
    });
    const probeStatus=document.createElement('button');
    probeStatus.textContent='Chrome-hangpróba eredménye';
    probeStatus.style.cssText=audioProbe.style.cssText;
    probeStatus.addEventListener('click',()=>nativeCommand('audioProbeStatus'));
    window.addEventListener('message',e=>{
      if(e.source!==window||e.origin!==location.origin||e.data?.type!==nativeReply)return;
      if(typeof e.data.payload?.probe==='string')label(e.data.payload.probe);
    });
    root.append(heading,description,btn,note,setup,chromeProbe,audioProbe,probeStatus);''')
page.write_text(s,encoding="utf-8")

tests=base/"test_project.py"
tests.write_text(tests.read_text(encoding="utf-8")+'''
service=(base/'app/src/main/java/hu/alya/yoda/ChromeAudioProbeService.java').read_text()
manifest=(base/'app/src/main/AndroidManifest.xml').read_text()
assert 'AudioPlaybackCaptureConfiguration.Builder(projection)' in service
assert 'addMatchingUid(chrome.uid)' in service
assert 'AudioRecord.READ_BLOCKING' in service
assert 'putString("status",message)' in service
assert 'FOREGROUND_SERVICE_MEDIA_PROJECTION' in manifest
assert 'android:foregroundServiceType="mediaProjection"' in manifest
assert 'startChromeAudioProbe' in (base/'app/src/main/java/hu/alya/yoda/MainActivity.java').read_text()
assert 'Chrome-hang átvételének tesztje' in (base/'app/src/main/assets/yodabridge/page.js').read_text()
''',encoding="utf-8")
print("PASS: Chrome capture feasibility probe - local amplitude only, explicit OS consent")
