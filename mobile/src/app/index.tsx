import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, Modal, TextInput, Alert, Linking, ScrollView } from 'react-native';
import axios from 'axios';
import { Feather } from '@expo/vector-icons';

// DİKKAT: Mac'inin IP adresini buraya yazdığından emin ol
const API_IP = "192.168.1.7"; 

const API_URL = `http://${API_IP}:8000/repos`;
const WS_URL = `ws://${API_IP}:8000/ws/repo-alerts`;

export default function App() {
  const [repos, setRepos] = useState<any[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [owner, setOwner] = useState('');
  const [repoName, setRepoName] = useState('');
  const [latestAlert, setLatestAlert] = useState<string | null>(null);

  // --- YENİ: Bildirim State'leri ---
  const [events, setEvents] = useState<any[]>([]);
  const [eventsModalVisible, setEventsModalVisible] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Uygulama açıldığında okunmamış bildirim sayısını çek
  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API_URL}/events/unread-count`);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error("Okunmamış sayısı çekilemedi:", error);
    }
  };

  // Zile basıldığında tüm geçmiş bildirimleri çek
  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API_URL}/events`);
      setEvents(response.data);
    } catch (error) {
      console.error("Bildirimler çekilemedi:", error);
    }
  };

  const fetchRepos = async () => {
    try {
      const response = await axios.get(`${API_URL}/track`);
      setRepos(response.data);
    } catch (error) {
      console.error("Repolar çekilemedi:", error);
    }
  };

  // Bir bildirime tıklandığında onu 'okundu' yap ve GitHub'a git
  const handleEventPress = async (event: any) => {
    if (!event.is_read) {
      try {
        await axios.post(`${API_URL}/events/${event.id}/read`);
        fetchUnreadCount(); // Rozeti güncelle
        fetchEvents(); // Listeyi güncelle
      } catch (error) {
        console.error("Okundu işaretlenemedi:", error);
      }
    }
    if (event.url) {
      Linking.openURL(event.url); // GitHub'ı tarayıcıda aç
    }
  };

  useEffect(() => {
    fetchRepos();
    fetchUnreadCount(); // Uygulama açıldığında okunmamış sayısını al

    const ws = new WebSocket(WS_URL);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Backend'den gelen dinamik title'ı (detaylı commit mesajı) basıyoruz
      setLatestAlert(data.title);
      
      // YENİ EKLENEN KISIM: Race Condition Çözümü
      // Backend'in veritabanına kaydetme (session.commit) işlemini 
      // bitirebilmesi için telefona yarım saniyelik bir gecikme ekliyoruz.
      setTimeout(() => {
        fetchRepos();
        fetchUnreadCount();
      }, 500);
      
      setTimeout(() => setLatestAlert(null), 4000);
    };

    return () => ws.close();
  }, []);

  const handleAddRepo = async () => {
    if (!owner || !repoName) return Alert.alert("Hata", "Tüm alanları doldurmalısın.");
    
    try {
      await axios.post(`${API_URL}/track`, {
        owner: owner.toLowerCase().trim(),
        repo_name: repoName.toLowerCase().trim(),
        added_by_user: "Admin"
      });
      
      setModalVisible(false);
      setOwner('');
      setRepoName('');
      fetchRepos();
    } catch (error) {
      Alert.alert("Hata", "Bu repo zaten ekli olabilir veya bulunamadı.");
    }
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.card}>
      <View>
        <Text style={styles.repoOwner}>{item.owner}</Text>
        <Text style={styles.repoName}>{item.repo_name}</Text>
      </View>
      <View style={[
        styles.statusDotBase, 
        { backgroundColor: item.last_known_commit_sha ? '#000000' : '#CCCCCC' }
      ]} />
    </View>
  );

  return (
    <View style={styles.container}>
      {latestAlert && (
        <View style={styles.toast}>
          <Feather name="bell" size={16} color="black" />
          <Text style={styles.toastText}>{latestAlert}</Text>
        </View>
      )}

      {/* Başlık ve Zil İkonu */}
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>Tracker.</Text>
        <TouchableOpacity 
          style={styles.bellIcon} 
          onPress={() => {
            fetchEvents();
            setEventsModalVisible(true);
          }}
        >
          <Feather name="bell" size={28} color="white" />
          {unreadCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{unreadCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <Text style={styles.subHeader}>Merhaba, Halil. Takipteki repoların:</Text>

      <FlatList
        data={repos}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderItem}
        contentContainerStyle={styles.listContainer}
      />

      <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
        <Feather name="plus" size={24} color="black" />
      </TouchableOpacity>

      {/* Yeni Repo Ekleme Modalı */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yeni Repo Ekle</Text>
            
            <TextInput 
              style={styles.input} 
              placeholder="Sahibi (Örn: tiangolo)" 
              placeholderTextColor="#666"
              value={owner} 
              onChangeText={setOwner} 
            />
            <TextInput 
              style={styles.input} 
              placeholder="Repo Adı (Örn: fastapi)" 
              placeholderTextColor="#666"
              value={repoName} 
              onChangeText={setRepoName} 
            />
            
            <TouchableOpacity style={styles.submitBtn} onPress={handleAddRepo}>
              <Text style={styles.submitBtnText}>Takibe Al</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelBtn} onPress={() => setModalVisible(false)}>
              <Text style={styles.cancelBtnText}>İptal</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Geçmiş Bildirimler Modalı */}
      <Modal visible={eventsModalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Bildirimler</Text>
              <TouchableOpacity onPress={() => setEventsModalVisible(false)}>
                <Feather name="x" size={24} color="white" />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={{ maxHeight: 400 }}>
              {events.length === 0 ? (
                <Text style={styles.emptyText}>Henüz bildirim yok.</Text>
              ) : (
                events.map((ev) => (
                  <TouchableOpacity 
                    key={ev.id} 
                    style={[styles.eventItem, !ev.is_read && styles.eventItemUnread]}
                    onPress={() => handleEventPress(ev)}
                  >
                    <Feather name="github" size={20} color={!ev.is_read ? "#0A84FF" : "#666"} />
                    <View style={styles.eventTextContainer}>
                      <Text style={[styles.eventTitle, !ev.is_read && styles.eventTitleUnread]}>
                        {ev.title}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>

    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000000', paddingTop: 60, paddingHorizontal: 20 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 },
  bellIcon: { position: 'relative', padding: 5 },
  badge: { position: 'absolute', top: 0, right: 0, backgroundColor: '#FF3B30', borderRadius: 10, width: 20, height: 20, justifyContent: 'center', alignItems: 'center', zIndex: 5 },
  badgeText: { color: 'white', fontSize: 12, fontWeight: 'bold' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 },
  emptyText: { textAlign: 'center', color: '#666', marginTop: 20 },
  eventItem: { flexDirection: 'row', alignItems: 'center', padding: 12, borderBottomWidth: 1, borderBottomColor: '#333' },
  eventItemUnread: { backgroundColor: '#222' }, 
  eventTextContainer: { marginLeft: 12, flex: 1 },
  eventTitle: { fontSize: 14, color: '#888' },
  eventTitleUnread: { color: '#FFF', fontWeight: 'bold' }, 
  headerTitle: { fontSize: 36, fontWeight: '900', color: '#FFFFFF', letterSpacing: -1 },
  subHeader: { fontSize: 16, color: '#888888', marginTop: 0, marginBottom: 20 },
  listContainer: { paddingBottom: 100 },
  card: { 
    backgroundColor: '#FFFFFF', padding: 20, borderRadius: 12, marginBottom: 15,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'
  },
  repoOwner: { fontSize: 12, color: '#666666', textTransform: 'uppercase', letterSpacing: 1 },
  repoName: { fontSize: 18, fontWeight: 'bold', color: '#000000', marginTop: 2 },
  statusDotBase: { width: 12, height: 12, borderRadius: 6 }, 
  fab: {
    position: 'absolute', bottom: 40, alignSelf: 'center',
    backgroundColor: '#FFFFFF', width: 60, height: 60, borderRadius: 30,
    justifyContent: 'center', alignItems: 'center',
    shadowColor: "#FFF", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 10,
  },
  toast: {
    position: 'absolute', top: 50, alignSelf: 'center', zIndex: 10,
    backgroundColor: '#FFFFFF', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 25,
    flexDirection: 'row', alignItems: 'center',
    shadowColor: "#FFF", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 10,
  },
  toastText: { marginLeft: 10, fontWeight: 'bold', color: '#000' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#111111', padding: 30, borderTopLeftRadius: 30, borderTopRightRadius: 30 },
  modalTitle: { fontSize: 24, fontWeight: 'bold', color: '#FFFFFF', marginBottom: 20 },
  input: { backgroundColor: '#222222', color: '#FFFFFF', padding: 15, borderRadius: 10, marginBottom: 15, fontSize: 16 },
  submitBtn: { backgroundColor: '#FFFFFF', padding: 15, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  submitBtnText: { color: '#000000', fontWeight: 'bold', fontSize: 16 },
  cancelBtn: { padding: 15, alignItems: 'center', marginTop: 5 },
  cancelBtnText: { color: '#888888', fontSize: 16 }
});