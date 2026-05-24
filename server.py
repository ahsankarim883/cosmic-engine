import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../auth/login_screen.dart';
import '../inspection/template_selector_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  void _signOut(BuildContext context) async {
    await Supabase.instance.client.auth.signOut();
    if (context.mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('COSMIC DASHBOARD'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: () => _signOut(context),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Welcome Card
              Card(
                color: const Color(0xFF2C3E50),
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Welcome back,',
                        style: TextStyle(color: Colors.white70, fontSize: 16),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        user?.email ?? 'Engineer',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Action Button
              ElevatedButton.icon(
                icon: const Icon(Icons.add_task),
                label: const Text('START NEW INSPECTION'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const TemplateSelectorScreen()),
                  );
                },
              ),
              const SizedBox(height: 32),

              // Recent Activity Title
              const Text(
                'Recent Certificates',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2C3E50),
                ),
              ),
              const SizedBox(height: 16),

              // Real-Time Database Stream
              Expanded(
                child: StreamBuilder<List<Map<String, dynamic>>>(
                  stream: Supabase.instance.client
                      .from('inspections')
                      .stream(primaryKey: ['id'])
                      .eq('engineer_id', user?.id ?? '')
                      .order('created_at', ascending: false), // Newest first
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(
                          child: CircularProgressIndicator(color: Color(0xFFF9A826)));
                    }
                    
                    if (!snapshot.hasData || snapshot.data!.isEmpty) {
                      return Center(
                        child: Text(
                          'No inspections yet. Start one above!',
                          style: TextStyle(color: Colors.grey.shade500),
                        ),
                      );
                    }

                    final inspections = snapshot.data!;

                    return ListView.builder(
                      itemCount: inspections.length,
                      itemBuilder: (context, index) {
                        final insp = inspections[index];
                        final payload = insp['payload'] ?? {};
                        final circuitName = payload['circuit_name'] ?? 'Unknown Circuit';
                        
                        // Grab the first 8 characters of the ID (Matches Python Script exactly)
                        final String fullId = insp['id'].toString();
                        final String shortId = fullId.length >= 8 ? fullId.substring(0, 8) : fullId;
                        
                        // The exact URL where the Python script puts the PDF
                        final pdfUrl = 'https://qxzydznbejrorfzjezxg.supabase.co/storage/v1/object/public/certificates/Certificate_$shortId.pdf';

                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          elevation: 2,
                          child: ListTile(
                            leading: const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 36),
                            title: Text(circuitName, style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: const Text('PDF Certificate Available'),
                            trailing: ElevatedButton(
                              onPressed: () {
                                _showPdfDialog(context, pdfUrl, circuitName);
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF2C3E50),
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                              ),
                              child: const Text('VIEW PDF'),
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // The dialog that gives the client the live link
  void _showPdfDialog(BuildContext context, String pdfUrl, String circuitName) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Certificate: $circuitName'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Our backend automation engine has processed your inspection.'),
            const SizedBox(height: 16),
            const Text('Secure PDF Link:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              color: Colors.grey.shade100,
              child: SelectableText(
                pdfUrl,
                style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              '👉 Highlight the link above, right-click, and select "Go to" or copy/paste it into a new tab.',
              style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('CLOSE'),
          ),
        ],
      ),
    );
  }
}
