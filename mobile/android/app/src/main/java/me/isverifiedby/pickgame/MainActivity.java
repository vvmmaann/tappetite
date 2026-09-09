package me.isverifiedby.pickgame;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import com.android.installreferrer.api.InstallReferrerClient;
import com.android.installreferrer.api.InstallReferrerStateListener;
import com.android.installreferrer.api.ReferrerDetails;
import com.getcapacitor.BridgeActivity;

/**
 * Tappetite main activity.
 *
 * Capacitor BridgeActivity wraps a WebView that loads https://isverifiedby.me.
 * The only thing this class adds is the Google Play Install Referrer plumbing
 * (added 2026-05-16 for v0.1.2):
 *
 *   1. On first launch, calls InstallReferrerClient.startConnection() to fetch
 *      the referrer string that Google Play captured at install time. Format
 *      is "ref=Uncle" (or empty if installed organically without a referrer
 *      query param).
 *   2. Stores the result in SharedPreferences so subsequent launches don't
 *      re-poll the InstallReferrer service (it's only valid for ~90 days
 *      post-install anyway).
 *   3. Exposes the value to the WebView via a @JavascriptInterface object
 *      named "AndroidInstall". Frontend reads it via:
 *           window.AndroidInstall.getInstallReferrer()
 *      Synchronous call, no async/race concerns once the InstallReferrer
 *      fetch has completed (which is fast — usually within 300ms of app start).
 *
 * Why no separate Capacitor plugin: the standard install would mean adding a
 * full Plugin class + TS wrapper + registration in capacitor.config. For one
 * method that returns one string, that's wildly overengineered. A direct
 * JavascriptInterface is 30 lines and zero plugin boilerplate.
 */
public class MainActivity extends BridgeActivity {
    private static final String TAG = "Tappetite";
    private static final String PREF_NAME = "tappetite_install";
    private static final String PREF_FETCHED = "install_referrer_fetched";
    private static final String PREF_REFERRER = "install_referrer_value";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Expose the JS interface to the WebView BEFORE any URL loads so that
        // window.AndroidInstall is available the moment frontend boots.
        try {
            WebView wv = this.bridge.getWebView();
            if (wv != null) {
                wv.addJavascriptInterface(new InstallReferrerBridge(this), "AndroidInstall");
            }
        } catch (Exception e) {
            Log.w(TAG, "Failed to attach AndroidInstall JS interface", e);
        }

        // Fetch the referrer asynchronously if we haven't already.
        SharedPreferences prefs = getSharedPreferences(PREF_NAME, MODE_PRIVATE);
        if (!prefs.getBoolean(PREF_FETCHED, false)) {
            fetchInstallReferrer(prefs);
        }
    }

    private void fetchInstallReferrer(final SharedPreferences prefs) {
        final InstallReferrerClient client = InstallReferrerClient.newBuilder(this).build();
        client.startConnection(new InstallReferrerStateListener() {
            @Override
            public void onInstallReferrerSetupFinished(int responseCode) {
                String referrer = "";
                if (responseCode == InstallReferrerClient.InstallReferrerResponse.OK) {
                    try {
                        ReferrerDetails details = client.getInstallReferrer();
                        referrer = details.getInstallReferrer();
                        if (referrer == null) referrer = "";
                        Log.i(TAG, "InstallReferrer: '" + referrer + "'");
                    } catch (Exception e) {
                        Log.w(TAG, "InstallReferrer.getInstallReferrer() failed", e);
                    }
                } else {
                    // FEATURE_NOT_SUPPORTED / SERVICE_UNAVAILABLE / DEVELOPER_ERROR.
                    // Mark as fetched anyway so we don't retry forever on devices
                    // that simply can't provide it (no Play Services etc).
                    Log.i(TAG, "InstallReferrer setup finished with code " + responseCode);
                }
                prefs.edit()
                    .putBoolean(PREF_FETCHED, true)
                    .putString(PREF_REFERRER, referrer)
                    .apply();
                try { client.endConnection(); } catch (Exception ignored) {}
            }

            @Override
            public void onInstallReferrerServiceDisconnected() {
                // Service died mid-connection. We did NOT mark as fetched in
                // SharedPreferences so a future cold launch will retry. No-op here.
            }
        });
    }

    /**
     * Minimal JS-callable bridge. Only exposes a single getter — no setters,
     * no side-effecting calls. Same-origin WebView loads our trusted domain,
     * so JavascriptInterface security warnings don't apply.
     */
    public static class InstallReferrerBridge {
        private final SharedPreferences prefs;

        public InstallReferrerBridge(Context ctx) {
            this.prefs = ctx.getSharedPreferences(PREF_NAME, MODE_PRIVATE);
        }

        @JavascriptInterface
        public String getInstallReferrer() {
            return prefs.getString(PREF_REFERRER, "");
        }
    }
}
