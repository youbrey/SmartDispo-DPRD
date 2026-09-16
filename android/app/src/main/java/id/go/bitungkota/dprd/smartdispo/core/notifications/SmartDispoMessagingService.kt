package id.go.bitungkota.dprd.smartdispo.core.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import dagger.hilt.android.AndroidEntryPoint
import id.go.bitungkota.dprd.smartdispo.core.model.DeviceRegistration
import id.go.bitungkota.dprd.smartdispo.core.network.SmartDispoApi
import id.go.bitungkota.dprd.smartdispo.core.security.deviceFingerprint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class SmartDispoMessagingService : FirebaseMessagingService() {
    @Inject lateinit var api: SmartDispoApi
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        scope.launch {
            runCatching { api.registerDevice(DeviceRegistration(deviceFingerprint(this@SmartDispoMessagingService), token)) }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val manager = getSystemService(NotificationManager::class.java)
        val channelId = "smartdispo_workflow"
        manager.createNotificationChannel(
            NotificationChannel(channelId, "Workflow SmartDispo", NotificationManager.IMPORTANCE_HIGH)
        )
        if (
            ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) return
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(id.go.bitungkota.dprd.smartdispo.R.drawable.ic_launcher_foreground)
            .setContentTitle(message.notification?.title ?: "SmartDispo")
            .setContentText(message.notification?.body ?: "Ada pembaruan workflow.")
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
        manager.notify(message.messageId?.hashCode() ?: System.currentTimeMillis().toInt(), notification)
    }
}
