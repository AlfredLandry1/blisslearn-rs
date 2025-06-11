# Guide d'Intégration BlissLearn API

Ce guide explique comment intégrer l'API BlissLearn avec différents frameworks et technologies.

## Table des Matières

1. [Next.js](#nextjs)
2. [React](#react)
3. [Vue.js](#vuejs)
4. [Angular](#angular)
5. [Mobile (React Native)](#react-native)
6. [Mobile (Flutter)](#flutter)

## Next.js

### Installation

```bash
npx create-next-app@latest blisslearn-next
cd blisslearn-next
npm install axios @tanstack/react-query
```

### Configuration

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/token', formData);
  return response.data;
};

export const getRecommendations = async (params: RecommendationRequest) => {
  const token = localStorage.getItem('token');
  const response = await api.post('/recommandations/', params, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.data;
};
```

### Exemple d'Utilisation

```typescript
// app/page.tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRecommendations } from '@/lib/api';

export default function Home() {
  const [objectives, setObjectives] = useState(['Python', 'Machine Learning']);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['recommendations', objectives],
    queryFn: () => getRecommendations({
      objectifs: objectives,
      niveau: 'Beginner',
      n_recommendations: 5
    })
  });

  if (isLoading) return <div>Chargement...</div>;
  if (error) return <div>Erreur: {error.message}</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Recommandations de Cours</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.map((course) => (
          <div key={course.titre} className="border p-4 rounded-lg">
            <h2 className="text-xl font-semibold">{course.titre}</h2>
            <p className="text-gray-600">{course.plateforme}</p>
            <p className="text-sm">{course.niveau}</p>
            <div className="mt-2">
              <p className="font-medium">Compétences :</p>
              <div className="flex flex-wrap gap-1">
                {course.skills.map((skill) => (
                  <span key={skill} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## React

### Installation

```bash
npm create vite@latest blisslearn-react -- --template react-ts
cd blisslearn-react
npm install axios @tanstack/react-query @mantine/core @mantine/hooks
```

### Configuration

```typescript
// src/api/blisslearn.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const BlissLearnApi = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/token', formData);
    return response.data;
  },
  
  getRecommendations: async (params: RecommendationRequest) => {
    const token = localStorage.getItem('token');
    const response = await api.post('/recommandations/', params, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  },
};
```

### Exemple d'Utilisation avec React Query et Mantine

```typescript
// src/components/RecommendationList.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, Text, Badge, Group, Stack } from '@mantine/core';
import { BlissLearnApi } from '../api/blisslearn';

export function RecommendationList() {
  const { data, isLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => BlissLearnApi.getRecommendations({
      objectifs: ['JavaScript', 'React', 'Node.js'],
      niveau: 'Intermediate',
      domaines_interet: ['Web Development'],
      n_recommendations: 5
    })
  });

  if (isLoading) {
    return <Text>Chargement des recommandations...</Text>;
  }

  return (
    <Stack spacing="md">
      {data?.map((course) => (
        <Card key={course.titre} shadow="sm" padding="lg">
          <Text size="lg" weight={500}>{course.titre}</Text>
          <Group spacing="xs" mt="xs">
            <Badge color="blue">{course.plateforme}</Badge>
            <Badge color="green">{course.niveau}</Badge>
            <Badge color="yellow">{course.duree}h</Badge>
          </Group>
          <Text size="sm" color="dimmed" mt="sm">
            {course.fournisseur}
          </Text>
          <Group spacing="xs" mt="md">
            {course.skills.map((skill) => (
              <Badge key={skill} variant="outline">
                {skill}
              </Badge>
            ))}
          </Group>
        </Card>
      ))}
    </Stack>
  );
}
```

## Vue.js

### Installation

```bash
npm create vue@latest blisslearn-vue
cd blisslearn-vue
npm install axios vue-query pinia
```

### Configuration avec Pinia

```typescript
// stores/recommendations.ts
import { defineStore } from 'pinia';
import axios from 'axios';

export const useRecommendationsStore = defineStore('recommendations', {
  state: () => ({
    recommendations: [],
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchRecommendations(params) {
      this.loading = true;
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post('http://localhost:8000/recommandations/', params, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        this.recommendations = response.data;
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    }
  }
});
```

### Exemple d'Utilisation

```vue
<!-- components/CourseList.vue -->
<template>
  <div class="course-list">
    <div v-if="loading">Chargement...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else class="grid">
      <div v-for="course in recommendations" :key="course.titre" class="course-card">
        <h3>{{ course.titre }}</h3>
        <div class="meta">
          <span class="platform">{{ course.plateforme }}</span>
          <span class="level">{{ course.niveau }}</span>
        </div>
        <div class="skills">
          <span v-for="skill in course.skills" :key="skill" class="skill-tag">
            {{ skill }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRecommendationsStore } from '@/stores/recommendations';

const store = useRecommendationsStore();

onMounted(async () => {
  await store.fetchRecommendations({
    objectifs: ['Vue.js', 'TypeScript', 'Frontend'],
    niveau: 'Intermediate',
    n_recommendations: 5
  });
});
</script>

<style scoped>
.course-list {
  padding: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.course-card {
  border: 1px solid #ddd;
  padding: 1rem;
  border-radius: 8px;
}

.skill-tag {
  background: #e9ecef;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin: 0.2rem;
  display: inline-block;
}
</style>
```

## React Native

### Installation

```bash
npx create-expo-app blisslearn-mobile
cd blisslearn-mobile
npm install axios @tanstack/react-query @react-navigation/native
```

### Configuration

```typescript
// src/api/blisslearn.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const getRecommendations = async (params: RecommendationRequest) => {
  const token = await AsyncStorage.getItem('token');
  const response = await api.post('/recommandations/', params, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.data;
};
```

### Exemple d'Utilisation

```typescript
// src/screens/RecommendationsScreen.tsx
import React from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { getRecommendations } from '../api/blisslearn';

export function RecommendationsScreen() {
  const { data, isLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => getRecommendations({
      objectifs: ['Mobile Development', 'React Native'],
      niveau: 'Intermediate',
      n_recommendations: 5
    })
  });

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Text>Chargement...</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={data}
      keyExtractor={(item) => item.titre}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.title}>{item.titre}</Text>
          <Text style={styles.platform}>{item.plateforme}</Text>
          <View style={styles.skillsContainer}>
            {item.skills.map((skill) => (
              <View key={skill} style={styles.skillTag}>
                <Text style={styles.skillText}>{skill}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: 'white',
    padding: 16,
    marginVertical: 8,
    borderRadius: 8,
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  platform: {
    color: '#666',
    marginTop: 4,
  },
  skillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  skillTag: {
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    margin: 2,
  },
  skillText: {
    color: '#1976d2',
    fontSize: 12,
  },
});
```

## Flutter

### Configuration

```dart
// lib/api/blisslearn_api.dart
import 'package:dio/dio.dart';
import 'package:shared_preferences.dart';

class BlissLearnApi {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    contentType: 'application/json',
  ));

  Future<List<Course>> getRecommendations({
    required List<String> objectives,
    String? level,
    List<String>? interests,
    int? duration,
    int recommendations = 5,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');

    final response = await _dio.post(
      '/recommandations/',
      data: {
        'objectifs': objectives,
        'niveau': level,
        'domaines_interet': interests,
        'duree_disponible': duration,
        'n_recommendations': recommendations,
      },
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
        },
      ),
    );

    return (response.data as List)
        .map((json) => Course.fromJson(json))
        .toList();
  }
}
```

### Exemple d'Utilisation

```dart
// lib/screens/recommendations_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class RecommendationsScreen extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendationsAsync = ref.watch(recommendationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Recommandations'),
      ),
      body: recommendationsAsync.when(
        loading: () => Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Erreur: $error')),
        data: (courses) => ListView.builder(
          itemCount: courses.length,
          itemBuilder: (context, index) {
            final course = courses[index];
            return Card(
              margin: EdgeInsets.all(8),
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      course.title,
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    SizedBox(height: 8),
                    Text(
                      course.platform,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    SizedBox(height: 8),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: course.skills.map((skill) => Chip(
                        label: Text(skill),
                        backgroundColor: Colors.blue[100],
                        labelStyle: TextStyle(color: Colors.blue[900]),
                      )).toList(),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
```

Chaque exemple d'intégration inclut :
- Configuration de base
- Gestion de l'authentification
- Appels API
- Interface utilisateur de base
- Gestion des états
- Gestion des erreurs

Choisissez le framework qui correspond le mieux à vos besoins et suivez les instructions d'intégration correspondantes. 